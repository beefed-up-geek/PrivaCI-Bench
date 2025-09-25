import json
import random
from pathlib import Path

def sample_dataset(input_file, output_file, dataset_name):
    compliant_cases = []
    violated_cases = []

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())

            if not data.get('violated_articles', []):
                compliant_cases.append(data)
            else:
                violated_cases.append(data)

    print(f"\n=== {dataset_name} ===")
    print(f"법을 준수한 케이스: {len(compliant_cases)}개")
    print(f"법을 위반한 케이스: {len(violated_cases)}개")

    random.seed(42)
    sampled_compliant = random.sample(compliant_cases, min(75, len(compliant_cases)))
    sampled_violated = random.sample(violated_cases, min(75, len(violated_cases)))

    print(f"샘플링된 준수 케이스: {len(sampled_compliant)}개")
    print(f"샘플링된 위반 케이스: {len(sampled_violated)}개")

    with open(output_file, 'w', encoding='utf-8') as f:
        for case in sampled_compliant + sampled_violated:
            f.write(json.dumps(case, ensure_ascii=False) + '\n')

    print(f"균형 잡힌 데이터셋이 {output_file}에 저장되었습니다.")

    return len(sampled_compliant), len(sampled_violated)

def main():
    datasets = [
        {
            'name': 'AI_ACT',
            'input': Path("HF_cache/cases/AI_ACT/data-00000-of-00001.jsonl"),
            'output': Path("HF_cache/cases/AI_ACT/balanced_sample.jsonl")
        },
        {
            'name': 'ACLU',
            'input': Path("HF_cache/cases/ACLU/data-00000-of-00001.jsonl"),
            'output': Path("HF_cache/cases/ACLU/balanced_sample.jsonl")
        }
    ]

    for dataset in datasets:
        sample_dataset(dataset['input'], dataset['output'], dataset['name'])

if __name__ == "__main__":
    main()