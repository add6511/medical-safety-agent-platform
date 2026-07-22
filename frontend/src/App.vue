<template>
  <router-view />
</template>

<script setup lang="ts">
import { useAppStore } from '@/stores/app'
const store = useAppStore()
store.loadUser()
</script>
