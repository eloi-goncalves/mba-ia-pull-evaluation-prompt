"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        username = os.getenv("USERNAME_LANGSMITH_HUB")
        repo_full_name = f"{username}/{prompt_name}"

        print(f"📤 Fazendo push para: {repo_full_name}")

        # Monta o ChatPromptTemplate a partir dos dados do YAML
        template = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system_prompt"]),
            ("human", prompt_data.get("user_prompt", "{bug_report}")),
        ])

        tags = prompt_data.get("tags", [])
        description = prompt_data.get("description", "")
        techniques = prompt_data.get("techniques_applied", [])
        if techniques:
            tags = list(set(tags + techniques))

        # Push público para o LangSmith Hub
        hub.push(
            repo_full_name,
            template,
            new_repo_is_public=True,
            new_repo_description=description,
            tags=tags if tags else None,
        )

        print(f"✅ Prompt publicado com sucesso: {repo_full_name}")
        print(f"   Tags: {tags}")
        print(f"   Descrição: {description}")
        return True

    except Exception as e:
        print(f"❌ Erro ao fazer push do prompt: {e}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    required_fields = ["description", "system_prompt", "version"]
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório faltando: {field}")

    system_prompt = prompt_data.get("system_prompt", "").strip()
    if not system_prompt:
        errors.append("system_prompt está vazio")

    if "TODO" in system_prompt:
        errors.append("system_prompt ainda contém TODOs")

    techniques = prompt_data.get("techniques_applied", [])
    if len(techniques) < 2:
        errors.append(
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}"
        )

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("Push Prompts to LangSmith Hub")

    # 1. Verifica variáveis de ambiente obrigatórias
    if not check_env_vars(["USERNAME_LANGSMITH_HUB"]):
        return 1

    # 2. Carrega o YAML do prompt otimizado (v2)
    prompts_file = (
        Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
    )
    print(f"📂 Carregando prompts de: {prompts_file}")

    yaml_data = load_yaml(str(prompts_file))

    if not yaml_data:
        print(f"❌ Não foi possível carregar: {prompts_file}")
        return 1

    # 3. Itera sobre os prompts definidos no YAML
    success_count = 0
    fail_count = 0

    for prompt_name, prompt_data in yaml_data.items():
        print_section_header(f"Processando: {prompt_name}", char="-", width=40)

        # Valida o prompt antes do push
        is_valid, errors = validate_prompt(prompt_data)
        if not is_valid:
            print("❌ Prompt inválido:")
            for error in errors:
                print(f"   - {error}")
            fail_count += 1
            continue

        # Faz o push para o LangSmith
        if push_prompt_to_langsmith(prompt_name, prompt_data):
            success_count += 1
        else:
            fail_count += 1

    # 4. Resumo final
    print_section_header("Resumo")
    print(f"✅ Publicados com sucesso: {success_count}")
    print(f"❌ Falhas: {fail_count}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
