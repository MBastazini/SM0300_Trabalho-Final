<script setup>
import { ref } from 'vue'

const backendStatus = ref('Testando...')
const ano = ref([])
const preco = ref([])
const km = ref([])

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

async function fetchDataOnix() {
  try {
    const response = await fetch('/api/dados/onix')
    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const data = await response.json()
    ano.value = data.ano
    preco.value = data.preco
    km.value = data.km
  } catch (error) {
    console.error('Erro ao buscar dados:', error)
  }
}

async function fetchDataDolphin() {
  try {
    const response = await fetch('/api/dados/dolphin')
    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const data = await response.json()
    ano.value = data.ano
    preco.value = data.preco
    km.value = data.km
  } catch (error) {
    console.error('Erro ao buscar dados:', error)
  }
}

testBackend()
</script>

<template>
  <main>
    <h1>SM0300 - Mínimos Quadrados</h1>
    <p>{{ backendStatus }}</p>
    <button type="button" @click="testBackend">Testar conexão</button>
    <!-- cria uma tabela com ano, km e preco  -->
    <!-- cria um botao preco_normalizado_onix e preco_normalizado_dolphin -->
    <button type="button" @click="fetchDataOnix">Preço Normalizado Onix</button>
    <button type="button" @click="fetchDataDolphin">Preço Normalizado Dolphin</button>
    <table>
      <thead>
        <tr>
          <th>Ano</th>
          <th>Preço</th>
          <th>Quilometragem</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(anoItem, index) in ano" :key="index">
          <td>{{ anoItem }}</td>
          <td>{{ preco[index] }}</td>
          <td>{{ km[index] }}</td>
        </tr>
      </tbody>
    </table>
  </main>
</template>
