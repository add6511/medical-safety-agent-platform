package com.medicalsafety.platform.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.medicalsafety.platform.dto.AiTriageRequest;
import com.medicalsafety.platform.dto.AiTriageResponse;
import com.medicalsafety.platform.dto.AiTriageSymptomRequest;
import com.medicalsafety.platform.dto.SubmitTriageResultRequest;
import com.medicalsafety.platform.dto.TriageResultResponse;
import com.medicalsafety.platform.entity.MedicalRecord;
import com.medicalsafety.platform.entity.PreConsultation;
import com.medicalsafety.platform.entity.Symptom;
import com.medicalsafety.platform.enums.PreConsultationStatus;
import com.medicalsafety.platform.enums.RoleType;
import com.medicalsafety.platform.exception.AccessDeniedException;
import com.medicalsafety.platform.exception.BusinessException;
import com.medicalsafety.platform.exception.ResourceNotFoundException;
import com.medicalsafety.platform.repository.MedicalRecordRepository;
import com.medicalsafety.platform.repository.PreConsultationRepository;
import com.medicalsafety.platform.repository.SymptomRepository;
import com.medicalsafety.platform.security.RequestContextHelper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class AiTriageOrchestrationService {

    private static final Set<String> STAFF_ROLES = Set.of(
            RoleType.MEDICAL_STAFF.name(),
            RoleType.ADMIN.name()
    );

    private final AiTriageClient aiTriageClient;
    private final TriageResultService triageResultService;
    private final PreConsultationRepository preConsultationRepository;
    private final MedicalRecordRepository medicalRecordRepository;
    private final SymptomRepository symptomRepository;
    private final RequestContextHelper requestContextHelper;
    private final ObjectMapper objectMapper;

    public TriageResultResponse analyzeAndPersist(
            Long preConsultationId,
            Long operatorId,
            List<String> roles) {

        PreConsultation preConsultation =
                preConsultationRepository
                        .findById(preConsultationId)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "预问诊记录不存在"
                                )
                        );

        checkAccess(preConsultation, operatorId, roles);
        prepareTriageStatus(preConsultation);

        MedicalRecord record =
                medicalRecordRepository
                        .findById(preConsultation.getRecordId())
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "预问诊关联的就诊记录不存在"
                                )
                        );

        List<Symptom> symptoms =
                symptomRepository.findByRecordId(
                        record.getId()
                );

        if (symptoms.isEmpty()) {
            throw new BusinessException(
                    "NO_SYMPTOMS",
                    "当前病例没有症状记录，无法执行AI分诊"
            );
        }

        String traceId = resolveTraceId();

        AiTriageRequest aiRequest =
                buildAiRequest(record, symptoms);

        AiTriageResponse aiResponse =
                aiTriageClient.analyze(
                        aiRequest,
                        traceId
                );

        SubmitTriageResultRequest resultRequest =
                buildResultRequest(
                        preConsultationId,
                        aiResponse
                );

        TriageResultResponse result =
                triageResultService
                        .submitInternalTriageResult(
                                resultRequest,
                                operatorId
                        );

        log.info(
                "AI_TRIAGE_ORCHESTRATION_COMPLETE "
                        + "| preConsultationId={} "
                        + "| triageResultId={} "
                        + "| riskLevel={} "
                        + "| traceId={}",
                preConsultationId,
                result.getId(),
                aiResponse.getRiskLevel(),
                traceId
        );

        return result;
    }

    private void checkAccess(
            PreConsultation preConsultation,
            Long operatorId,
            List<String> roles) {

        boolean isStaff =
                roles != null
                        && roles.stream()
                        .anyMatch(STAFF_ROLES::contains);

        if (isStaff) {
            return;
        }

        if (!preConsultation
                .getPatientId()
                .equals(operatorId)) {

            throw new AccessDeniedException(
                    "无权对该预问诊执行AI分诊"
            );
        }
    }

    private void prepareTriageStatus(
            PreConsultation preConsultation) {

        PreConsultationStatus status =
                preConsultation.getStatus();

        if (status == PreConsultationStatus.INITIATED) {
            preConsultation.setStatus(
                    PreConsultationStatus.SYMPTOM_COLLECTED
            );

            preConsultationRepository.save(
                    preConsultation
            );

            return;
        }

        if (status != PreConsultationStatus.SYMPTOM_COLLECTED
                && status != PreConsultationStatus.NEEDS_REVISION) {

            throw new BusinessException(
                    "INVALID_AI_TRIAGE_STATE",
                    "当前状态不能执行AI分诊: " + status
            );
        }
    }

    private AiTriageRequest buildAiRequest(
            MedicalRecord record,
            List<Symptom> symptoms) {

        List<AiTriageSymptomRequest> aiSymptoms =
                symptoms.stream()
                        .map(this::buildAiSymptom)
                        .toList();

        return AiTriageRequest.builder()
                .caseId(record.getCaseCode())
                .age(null)
                .symptoms(aiSymptoms)
                .redFlags(detectRedFlags(symptoms))
                .freeText(buildFreeText(record))
                .modelSuggestedRisk(null)
                .build();
    }

    private AiTriageSymptomRequest buildAiSymptom(
            Symptom symptom) {

        return AiTriageSymptomRequest.builder()
                .name(symptom.getSymptomName())
                .severity(
                        mapSeverity(symptom)
                )
                .duration(
                        symptom.getDurationDesc() == null
                                ? ""
                                : symptom.getDurationDesc()
                )
                .build();
    }

    private int mapSeverity(Symptom symptom) {
        if (symptom.getSeverity() == null) {
            return 5;
        }

        return switch (symptom.getSeverity()) {
            case MILD -> 3;
            case MODERATE -> 6;
            case SEVERE -> 9;
        };
    }

    private List<String> detectRedFlags(
            List<Symptom> symptoms) {

        Set<String> flags =
                new LinkedHashSet<>();

        for (Symptom symptom : symptoms) {
            String name =
                    symptom.getSymptomName()
                            .toLowerCase(Locale.ROOT);

            if (containsAny(
                    name,
                    "意识改变",
                    "意识不清",
                    "昏迷",
                    "神志不清")) {

                flags.add("consciousness_change");
            }

            if (containsAny(
                    name,
                    "严重呼吸困难",
                    "喘不过气",
                    "呼吸急促")) {

                flags.add(
                        "severe_breathing_difficulty"
                );
            }

            if (containsAny(
                    name,
                    "持续胸部不适",
                    "持续胸痛",
                    "胸部压迫感")) {

                flags.add(
                        "persistent_chest_discomfort"
                );
            }

            if (containsAny(
                    name,
                    "无法控制的出血",
                    "大量出血",
                    "持续出血")) {

                flags.add(
                        "uncontrolled_bleeding"
                );
            }

            if (containsAny(
                    name,
                    "自伤",
                    "自杀",
                    "伤害自己")) {

                flags.add("self_harm_risk");
            }

            boolean pregnancySignal =
                    containsAny(
                            name,
                            "妊娠",
                            "怀孕",
                            "孕期"
                    )
                    && containsAny(
                            name,
                            "出血",
                            "剧痛",
                            "昏厥",
                            "晕厥"
                    );

            if (pregnancySignal) {
                flags.add(
                        "pregnancy_emergency_signal"
                );
            }
        }

        return new ArrayList<>(flags);
    }

    private boolean containsAny(
            String text,
            String... keywords) {

        for (String keyword : keywords) {
            if (text.contains(keyword)) {
                return true;
            }
        }

        return false;
    }

    private String buildFreeText(
            MedicalRecord record) {

        List<String> parts = new ArrayList<>();

        addPart(
                parts,
                "主诉",
                record.getChiefComplaint()
        );

        addPart(
                parts,
                "现病史",
                record.getPresentIllness()
        );

        addPart(
                parts,
                "既往史",
                record.getPastHistory()
        );

        addPart(
                parts,
                "过敏史",
                record.getAllergyHistory()
        );

        return String.join("；", parts);
    }

    private void addPart(
            List<String> parts,
            String label,
            String value) {

        if (value != null && !value.isBlank()) {
            parts.add(label + "：" + value);
        }
    }

    private SubmitTriageResultRequest buildResultRequest(
            Long preConsultationId,
            AiTriageResponse aiResponse) {

        return SubmitTriageResultRequest.builder()
                .preConsultationId(preConsultationId)
                .urgencyLevel(
                        mapUrgency(
                                aiResponse.getRiskLevel()
                        )
                )
                .suggestedDepartment(
                        "待医务人员确认"
                )
                .riskFlags(
                        buildRiskFlagsJson(aiResponse)
                )
                .reasoningSummary(
                        buildReasoningSummary(aiResponse)
                )
                .referenceSources(
                        buildReferenceSourcesJson(
                                aiResponse
                        )
                )
                .build();
    }

    private String mapUrgency(String riskLevel) {
        if (riskLevel == null) {
            return "ROUTINE";
        }

        return switch (
                riskLevel.toUpperCase(Locale.ROOT)
        ) {
            case "CRITICAL" -> "EMERGENCY";
            case "HIGH" -> "URGENT";
            case "MEDIUM" -> "SEMI_URGENT";
            default -> "ROUTINE";
        };
    }

    private String buildRiskFlagsJson(
            AiTriageResponse response) {

        Map<String, Object> data =
                new LinkedHashMap<>();

        data.put(
                "redFlags",
                response.getRedFlags()
        );

        data.put(
                "safetyFlags",
                response.getSafetyFlags()
        );

        data.put(
                "safetyStatus",
                response.getSafetyStatus()
        );

        data.put(
                "needsHumanReview",
                response.getNeedsHumanReview()
        );

        return toJson(data);
    }

    private String buildReferenceSourcesJson(
            AiTriageResponse response) {

        Map<String, Object> data =
                new LinkedHashMap<>();

        data.put(
                "citations",
                response.getCitations()
        );

        data.put(
                "evidence",
                response.getEvidence()
        );

        data.put(
                "traceId",
                response.getTraceId()
        );

        return toJson(data);
    }

    private String buildReasoningSummary(
            AiTriageResponse response) {

        List<String> parts = new ArrayList<>();

        addPart(
                parts,
                "症状摘要",
                response.getSymptomSummary()
        );

        addPart(
                parts,
                "风险等级",
                response.getRiskLevel()
        );

        addPart(
                parts,
                "安全状态",
                response.getSafetyStatus()
        );

        addPart(
                parts,
                "免责声明",
                response.getDisclaimer()
        );

        return String.join("；", parts);
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(
                    value
            );
        } catch (JsonProcessingException e) {
            throw new BusinessException(
                    "AI_RESULT_SERIALIZATION_FAILED",
                    "AI分诊结果序列化失败"
            );
        }
    }

    private String resolveTraceId() {
        String traceId =
                requestContextHelper.getTraceId();

        if (traceId == null || traceId.isBlank()) {
            return UUID.randomUUID().toString();
        }

        return traceId;
    }
}