"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header
from evaluate import pull_prompt_from_langsmith

load_dotenv()


def pull_prompts_from_langsmith():
    output_path = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v1.yml"

    try:
        prompt_data = pull_prompt_from_langsmith("leonanluppi/bug_to_user_story_v1")
        if not prompt_data:
            print("❌ Nenhum dado retornado do Hub.")
            return False

        # Salvando o prompt localmente
        if save_yaml(prompt_data, output_path):
            print(f"✅ Prompts salvos em: {output_path}")
            return True
        else:
            print("❌ Falha ao salvar os prompts localmente.")
            return False
    except Exception as e:
        print(f"❌ Erro ao puxar prompts do Hub: {e}")
        return False  


def main():
    """Função principal"""
    print_section_header("1 - Executando o pull dos prompts do LangSmith")
    pull_prompts_from_langsmith()


if __name__ == "__main__":
    sys.exit(main())
