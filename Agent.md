# PrivaCI-Bench Project Analysis

## Project Overview
PrivaCI-Bench is a benchmark project for evaluating legal compliance with privacy regulations (GDPR, HIPAA, AI ACT, ACLU). It uses various AI models to determine whether data transfer scenarios are permitted, prohibited, or not applicable under specific regulations.

## Key Components

### 1. Data Structure

#### Knowledge Base (KBs)
- **Location**: `HF_cache/KBs/`
- **Domains**: GDPR, HIPAA, AI_ACT
- **Structure**: 
  ```
  ['reference', 'norm_type', 'sender', 'sender_role', 'recipient', 'recipient_role', 
   'subject', 'subject_role', 'information_type', 'consent_form', 'purpose', 
   'sender_is_subject', 'recipient_is_subject', 'regulation_id', 'regulation_content']
  ```

#### Case Dataset (cases)
- **Location**: `HF_cache/cases/`
- **Domains**: GDPR, HIPAA, AI_ACT, ACLU
- **Structure**:
  ```
  ['norm_type', 'sender', 'sender_role', 'recipient', 'recipient_role', 
   'subject', 'subject_role', 'information_type', 'consent_form', 'purpose', 
   'followed_articles', 'violated_articles', 'case_content']
  ```

### 2. Core Execution Scripts

#### 2.1 direct_answer.py
**Purpose**: Direct answer approach for compliance judgment

**Execution Flow**:
1. **Data Loading**: Load local datasets with `get_local_KB_dataset()`, `get_local_case_dataset()`
2. **Model Initialization**: Set up HuggingFace model or API model
3. **Agent Creation**: Create agent using `AgentAction` class
   - Template: `prompts/direct_answer_prompt.txt`
   - Parser: `LlamaParser().parse_decision`
4. **Case Processing**:
   - Iterate through each domain (GDPR+HIPAA+AI_ACT+ACLU)
   - Extract CI elements for each case (sender, recipient, subject, information_type, etc.)
   - Query model using `agents.complete()`
   - Transform results using `label_transform()` and calculate accuracy

**Key Code Location**: `/Users/taeyoonkwack/Documents/PrivaCI-Bench/direct_answer.py:28-92`

#### 2.2 cot_auto_answer.py
**Purpose**: Chain-of-Thought automatic reasoning approach

**Execution Flow**:
- Similar to direct_answer.py but uses `parse_cot_auto` parser
- Template: `prompts/cot-answer-prompt-auto.txt`
- Generates answers through more detailed reasoning process

#### 2.3 search_content_for_answer.py
**Purpose**: Search-based approach using relevant regulations

**Execution Flow**:
1. **Agent Creation**: Uses `AgentContentSearch`
2. **Multi-step Processing**:
   - Step 1: `lawyer_agent` analyzes event with domain knowledge
   - Step 2: `search_agent` searches related regulations (`search_related_regulations`)
   - Step 3: `law_filter_agent` filters candidate regulations
   - Step 4: `law_judge_agent` judges regulation applicability
   - Step 5: `decision_agent` makes final decision

**Key Code Location**: `/Users/taeyoonkwack/Documents/PrivaCI-Bench/search_content_for_answer.py:46-115`

#### 2.4 MCQ_qwq.py
**Purpose**: Multiple choice question format evaluation

**Execution Flow**:
- Load MCQ datasets (easy/medium/hard)
- Use `parse_MCQ` parser for A/B/C/D choice parsing

### 3. Agent System

#### 3.1 AgentAction Class
**Location**: `/Users/taeyoonkwack/Documents/PrivaCI-Bench/agents/agents.py:55-115`

**Role**: 
- Base agent class
- Supports both HuggingFace models and OpenAI API
- Template-based prompt generation
- Response parsing

**Key Methods**:
- `load_template()`: Load prompt template
- `complete()`: Query model and return parsed results

#### 3.2 AgentContentSearch Class
**Location**: `/Users/taeyoonkwack/Documents/PrivaCI-Bench/agents/agents.py:354-466`

**Role**: 
- Content-based search for decision making
- Related regulation search using BM25
- Multi-step filtering and judgment process

**Key Components**:
- `lawyer_agent`: Initial analysis
- `search_agent`: Regulation search (uses AgentSearch class)
- `law_judge_agent`: Regulation applicability judgment
- `decision_agent`: Final decision

### 4. Utilities and Parsers

#### 4.1 LlamaParser Class
**Location**: `/Users/taeyoonkwack/Documents/PrivaCI-Bench/parse_string.py:3-231`

**Key Parsing Methods**:
- `parse_decision()`: Final decision parsing (positive/negative/not applicable)
- `parse_cot_auto()`: CoT-style answer parsing
- `parse_MCQ()`: Multiple choice answer parsing

#### 4.2 Utility Functions
**Location**: `/Users/taeyoonkwack/Documents/PrivaCI-Bench/utils.py`

- `label_transform()`: Label transformation (e.g., 'prohibited' → ['negative', 'prohibit', 'prohibited'])
- `Trie class`: Regulation ID hierarchy management
- `log()`: Logging function

### 5. Prompt System

**Location**: `prompts/` directory

**Key Templates**:
- `direct_answer_prompt.txt`: Basic template for direct answers
- `cot-answer-prompt-auto.txt`: CoT automatic reasoning template
- `cot-knowledge-lookup-prompt.txt`: Knowledge search template

**Template Structure**:
```
Determine the relationship between the provided event and the {domain} regulations.
(A) The event is prohibited by {domain}.
(B) The event is permitted by {domain}.
(C) The event is not related to {domain}.

Event: {event}
Output Format: Choice: [A. Prohibited | B. Permitted | C. Not related ]
```

## Execution Example Analysis

### README.md Example Execution Flow

#### 1. Basic Execution
```bash
python direct_answer.py --log_path logs/dp/qwen2.txt --model Qwen/Qwen2.5-7B-Instruct --domain 'GDPR+HIPAA+AI_ACT+ACLU'
```

**Execution Process**:
1. **Setup**: Seed setting, logging path setup
2. **Data Loading**: Load KB and case datasets
3. **Model Initialization**: Wrap Qwen model with HuggingfaceChatbot
4. **Domain Processing**: For each domain (GDPR, HIPAA, AI_ACT, ACLU)
5. **Case Evaluation**: Extract CI elements for each case, then query model
6. **Result Calculation**: Calculate accuracy and logging

#### 2. API Model Execution
```bash
python direct_answer.py --log_path logs/dp/openai.txt --domain 'GDPR+HIPAA+AI_ACT+ACLU' --api_model gpt-4o-mini --api_name gpt-4o-mini
```

**Difference**: Uses OpenAI API instead of HuggingFace model

#### 3. Notebook Demo (gdpr_gpt4o_demo.ipynb)
**Execution Flow**:
1. **Sample Data Preparation**: Create GDPR-related data transfer scenario
2. **Prompt Construction**: Generate natural language prompt including CI elements
3. **Model Query**: Query GPT-4o-mini for compliance
4. **Result Analysis**: Determine permitted/prohibited/not applicable

## Core Architecture Features

### 1. Modular Design
- Each script can run independently
- Shared common utilities and agent system

### 2. Multiple Reasoning Approaches
- **Direct Answer**: Simple direct responses
- **CoT (Chain-of-Thought)**: Step-by-step reasoning
- **Content Search**: Search relevant regulations then judge

### 3. Multi-modal Evaluation
- Text-based case analysis
- Multiple choice question (MCQ) evaluation

### 4. Extensible Domain System
- Supports GDPR, HIPAA, AI ACT, ACLU
- Easy to add new regulatory domains

This project provides a systematic benchmark system for comprehensively evaluating AI models' understanding of legal compliance.