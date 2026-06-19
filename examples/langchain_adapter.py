"""LangChain adapter example.

Requires: pip install tripwire[langchain] langchain-openai
"""

from tripwire import Budget, BudgetExceeded
from tripwire.adapters.langchain import TripwireCallbackHandler


def main():
    budget = Budget(max_usd=0.50, max_calls=20)
    handler = TripwireCallbackHandler(budget)

    # Use with any LangChain LLM:
    # from langchain_openai import ChatOpenAI
    # llm = ChatOpenAI(model="gpt-4o", callbacks=[handler])
    # with budget:
    #     response = llm.invoke("Explain quantum computing in one sentence")
    #     print(response.content)

    print("LangChain adapter ready. Attach `handler` to your LLM callbacks.")
    print(f"Budget: max_usd=$0.50, max_calls=20")


if __name__ == "__main__":
    main()
