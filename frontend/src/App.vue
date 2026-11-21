<script setup>
import { ref } from 'vue'

const backendStatus = ref('Testando...')

async function testBackend() {
  backendStatus.value = 'Testando...'

  try {
    const response = await fetch('/api/test')
    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const data = await response.json()
    backendStatus.value = data.message
  } catch (error) {
    backendStatus.value = `Erro ao conectar ao backend: ${error.message}`
  }
}

testBackend()
</script>

<template>
  <main>
    <h1>SM0300 - Mínimos Quadrados</h1>
    <p>{{ backendStatus }}</p>
    <button type="button" @click="testBackend">Testar conexão</button>
  </main>
</template>
