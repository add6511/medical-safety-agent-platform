import { PrismaClient, UserRole, UserStatus, RuleType, RuleStatus } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  const passwordHash = await bcrypt.hash("demo1234", 10);

  const admin = await prisma.user.create({
    data: {
      username: "admin_demo",
      passwordHash,
      role: UserRole.admin,
      realName: "管理员",
      phone: "13800000001",
      status: UserStatus.active,
    },
  });

  const doctor = await prisma.user.create({
    data: {
      username: "doctor_demo",
      passwordHash,
      role: UserRole.doctor,
      realName: "张医生",
      phone: "13800000002",
      status: UserStatus.active,
    },
  });

  const follower = await prisma.user.create({
    data: {
      username: "follower_demo",
      passwordHash,
      role: UserRole.follower,
      realName: "李随访",
      phone: "13800000003",
      status: UserStatus.active,
    },
  });

  const patient = await prisma.user.create({
    data: {
      username: "patient_demo",
      passwordHash,
      role: UserRole.patient,
      realName: "王患者",
      phone: "13800000004",
      status: UserStatus.active,
    },
  });

  await prisma.simulatedPatient.create({
    data: {
      userId: patient.userId,
      caseTag: "synthetic",
      ageGroup: "middle",
      gender: "male",
      medicalHistorySummary: "高血压病史5年，目前服用氨氯地平",
    },
  });

  await prisma.ruleEngineRule.createMany({
    data: [
      {
        ruleType: RuleType.red_flag,
        name: "胸痛红旗症状",
        condition: JSON.stringify({ symptomNames: ["胸痛", "胸闷", "心前区疼痛"] }),
        description: "胸痛相关症状为红旗症状，需重点关注心血管风险",
        status: RuleStatus.active,
        version: "v1",
      },
      {
        ruleType: RuleType.red_flag,
        name: "头痛红旗症状",
        condition: JSON.stringify({ symptomNames: ["剧烈头痛", "突发头痛", "喷射性呕吐"] }),
        description: "突发剧烈头痛为红旗症状，需排除脑血管意外",
        status: RuleStatus.active,
        version: "v1",
      },
      {
        ruleType: RuleType.contraindication,
        name: "高血压用药禁忌",
        condition: JSON.stringify({ keywords: ["高血压", "氨氯地平", "硝苯地平"] }),
        description: "高血压患者使用钙通道阻滞剂需注意禁忌",
        status: RuleStatus.active,
        version: "v1",
      },
      {
        ruleType: RuleType.contraindication,
        name: "糖尿病用药禁忌",
        condition: JSON.stringify({ keywords: ["糖尿病", "二甲双胍", "胰岛素"] }),
        description: "糖尿病患者用药需注意禁忌条件",
        status: RuleStatus.active,
        version: "v1",
      },
    ],
  });

  await prisma.medicalGuideline.create({
    data: {
      title: "高血压基层诊疗指南（2024年版）",
      sourceOrg: "国家心血管病中心",
      publishDate: new Date("2024-01-01"),
      category: "心血管",
      content: "本指南适用于基层医疗机构高血压的预防、诊断、治疗和随访管理...",
      status: "active",
      version: "v1",
    },
  });

  await prisma.modelConfig.create({
    data: {
      modelVersion: "glm-4",
      promptVersion: "v1.0",
      knowledgeBaseVersion: "v1.0",
      isActive: true,
      updatedBy: admin.userId,
    },
  });

  console.log("Seed data created successfully");
  console.log({ admin: admin.userId, doctor: doctor.userId, follower: follower.userId, patient: patient.userId });
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });