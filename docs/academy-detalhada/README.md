# 📚 Academia Detalhada - Versão Completa

> **Tempo total:** ~8 horas de estudo aprofundado
> **Para quem:** Quem quer dominar TODOS os aspectos técnicos do projeto

---

## 📖 Sobre Esta Versão

Esta é a **versão completa e detalhada** da Academia Mini PACS AI, com explicações aprofundadas, diagramas, exemplos de código e referências científicas.

**Se você quer uma visão geral rápida (30 min), veja:** [../ACADEMY.md](../ACADEMY.md)

---

## 📚 Módulos Disponíveis

### [Módulo 1: Fundamentos de Imagens Médicas](./modulo1-fundamentos-pacs-dicom.md)
**Duração:** 45-60 minutos

- O que é PACS? (história, componentes, benefícios)
- Padrão DICOM completo (estrutura, tags, hierarquia)
- Orthanc: arquitetura, REST API, configuração
- Workflow radiológico (tradicional vs com IA)
- Protocolos: C-STORE, C-FIND, C-MOVE, HL7

### [Módulo 2: Inteligência Artificial em Radiologia](./modulo2-ia-radiologia.md)
**Duração:** 60-75 minutos

- Deep Learning para Raio-X (CNNs explicadas)
- Dataset NIH ChestX-ray14 (112.120 imagens)
- TorchXRayVision (instalação, uso, modelos)
- DenseNet121 (arquitetura completa)
- Transfer Learning vs Training from Scratch
- Performance e métricas (AUC-ROC)

### [Módulo 3: Explicabilidade e Interpretabilidade](./modulo3-explicabilidade.md)
**Duração:** 90-120 minutos

- Por que explicabilidade importa (regulamentação)
- Grad-CAM: algoritmo completo passo a passo
- Implementação detalhada (hooks, gradientes, weighted sum)
- Máscaras de segmentação (threshold adaptativo)
- Ground Truth vs Grad-CAM (quando usar cada um)
- Comparação com xray_masks.ipynb do TorchXRayVision

### [Módulo 4: Arquitetura da Aplicação](./modulo4-arquitetura.md)
**Duração:** 90-120 minutos

- Visão geral completa do sistema
- Container Orthanc (SQLite, filesystem, persistência)
- API FastAPI (endpoints, carregamento de modelo)
- Jupyter (Docker, volume mapping, notebooks)
- Comunicação entre serviços (DNS, rede Docker)
- Fluxo de requisição completo

### [Módulo 5: Implementação Técnica](./modulo5-implementacao.md)
**Duração:** 120-150 minutos

- Pré-processamento DICOM (método oficial vs anterior)
- Comparação experimental (11% de diferença)
- Pipeline de inferência (código completo)
- Geração de heatmaps e máscaras (implementação)
- Validação científica com IoU
- Threshold adaptativo (decisões técnicas)

### [Módulo 6: Discovery e Insights de Desenvolvimento](./modulo6-discovery.md)
**Duração:** 60-90 minutos

- Desafios encontrados (erro 422, 500, Docker)
- Decisões de arquitetura (justificativas)
- Evolução do projeto (v1.0.0 → v1.3.0+)
- Lições aprendidas
- Features implementadas vs planejadas

### [Módulo 7: Uso Clínico e Regulamentação](./modulo7-uso-clinico.md)
**Duração:** 90-120 minutos

- CAD vs Diagnostic AI (diferenças legais)
- Responsabilidades do médico radiologista
- FDA (Class II Medical Device)
- ANVISA (RDC 44/2023)
- GDPR (Right to explanation)
- Validação clínica (estudos necessários)
- Limitações técnicas e clínicas

---

## 🎓 Como Usar Esta Versão Detalhada

### Opção 1: Sequencial (Recomendado)
Leia os módulos em ordem, do 1 ao 7. Cada módulo assume conhecimento dos anteriores.

### Opção 2: Por Perfil

**Desenvolvedor Backend:**
```
Módulo 1 → Módulo 4 → Módulo 5 → Módulo 6
(~5 horas)
```

**Data Scientist / Pesquisador:**
```
Módulo 2 → Módulo 3 → Módulo 5 → Módulo 6
(~6 horas)
```

**Médico Radiologista:**
```
Módulo 1 → Módulo 2 (básico) → Módulo 3 → Módulo 7
(~5 horas)
```

**Trilha Completa:**
```
Módulos 1 → 2 → 3 → 4 → 5 → 6 → 7
(~8 horas)
```

---

## 📊 Comparação: Versão Resumida vs Detalhada

| Aspecto | Resumida ([ACADEMY.md](../ACADEMY.md)) | Detalhada (aqui) |
|---------|----------------------------------------|------------------|
| **Tempo** | 30 minutos | ~8 horas |
| **Formato** | 1 arquivo | 7 módulos |
| **Linhas** | 471 | ~2.700 |
| **Exemplos** | Essenciais | Completos |
| **Diagramas** | Básicos | Detalhados |
| **Código** | Snippets | Implementação completa |
| **Referências** | Principais | Extensivas |
| **Público** | Visão geral | Domínio profundo |

---

## 🎯 Objetivos de Aprendizado (Versão Detalhada)

Ao completar todos os 7 módulos detalhados, você será capaz de:

✅ Explicar TODOS os aspectos técnicos do projeto
✅ Implementar sistemas similares do zero
✅ Modificar e estender o código existente
✅ Tomar decisões de arquitetura fundamentadas
✅ Validar cientificamente resultados
✅ Compreender regulamentação profundamente
✅ Treinar outros desenvolvedores/médicos

---

## 💡 Dicas para Estudo Aprofundado

1. **Reserve tempo:** Cada módulo demora 1-2h
2. **Execute os exemplos:** Todos os códigos são funcionais
3. **Consulte os papers:** Links para artigos científicos incluídos
4. **Faça anotações:** Conceitos complexos requerem revisão
5. **Teste no sistema:** Valide o aprendizado com código real

---

## 📚 Recursos Adicionais

Além dos módulos, consulte:

- **Código fonte:** `inference_api/app/` - Implementação real
- **Notebook:** `notebooks/orthanc_analysis.ipynb` - Aplicação prática
- **Documentação técnica:** `docs/API.md`, `docs/MODELO_IA.md`, etc.
- **Papers científicos:** Links nos módulos

---

**Versão:** 1.3.0+ | **Data:** 2025-11-04 | **Autor:** Wendell Barreto

**Comece aqui:** [Módulo 1 - Fundamentos de Imagens Médicas](./modulo1-fundamentos-pacs-dicom.md) →
