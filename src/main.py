import asyncio
from orchestrator import KnowledgeOrchestrator


async def main():
    print("=" * 60)
    print("        AI KNOWLEDGE HUB - MULTI-AGENT SYSTEM")
    print("=" * 60)

    folder_name = input("\nEnter your folder name (default: viola): ").strip()
    if not folder_name:
        folder_name = "viola"

    question = input("Ask your question: ").strip()
    if not question:
        print("\n[Error] Question cannot be empty.")
        return

    orchestrator = KnowledgeOrchestrator()

    print("\nRunning multi-agent pipeline...")
    result = await orchestrator.run(question, folder_name)
    primary = result.get("primary_sources", [])
    fallback = result.get("fallback_sources", [])
    router_line = f"Router selected: {', '.join(primary) or 'none'}"
    if fallback:
        router_line += f" -> found nothing, expanded to: {', '.join(fallback)}"
    print(router_line)

    print("\n" + "=" * 60)
    print("                     ANSWER")
    print("=" * 60)
    print(result["answer"])

    print("\n" + "-" * 60)
    validation = result.get("validation", {})
    print(f"Validation Status: {validation.get('status')}")
    print(f"Validation Reason: {validation.get('reason')}")

    print("\nSources Used:")
    docs = result.get("documents", [])
    if not docs:
        print("  (No sources found)")
    else:
        for doc in docs:
            print(f"  - {doc['file_name']} (Score: {doc['score']:.2f})")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())