"""Golden benchmark cases: natural prompts + expected answers.

Every prompt is unique (the headline benchmark run contains no
repeats — cache effects are measured in a separate, labelled
scenario). Prompts are written the way a user would write them, not
stuffed with classifier keywords; one case (``hard-short``) is a
short prompt the heuristic classifier predictably under-routes, and
its measured quality loss is reported, not hidden.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkCase:
    """One golden case: prompt, expected answer, traffic class."""

    prompt: str
    expected: str
    kind: str


CASES: tuple[BenchmarkCase, ...] = (
    # --- simple factual (one-sentence answers) ---
    BenchmarkCase("What is the capital of France?",
                  "Paris is the capital of France.", "simple"),
    BenchmarkCase("What is 12 + 7?",
                  "12 + 7 equals 19.", "simple"),
    BenchmarkCase("Translate 'thank you' into French.",
                  "Merci is how you say thank you in French.", "simple"),
    BenchmarkCase("What is the boiling point of water at sea level?",
                  "Water boils at 100 degrees Celsius at sea level.", "simple"),
    BenchmarkCase("What currency is used in Japan?",
                  "The yen is the currency used in Japan.", "simple"),
    BenchmarkCase("How many sides does a hexagon have?",
                  "A hexagon has six sides.", "simple"),
    BenchmarkCase("Name the gas giant planets in our solar system.",
                  "Jupiter and Saturn are the gas giant planets.", "simple"),
    BenchmarkCase("Define photosynthesis in one sentence.",
                  "Photosynthesis is how plants convert sunlight, water and carbon "
                  "dioxide into oxygen and glucose.", "simple"),
    # --- medium writing/explanation (three-sentence answers) ---
    BenchmarkCase(
        "Write a short product description for a ceramic coffee mug aimed at "
        "remote workers who enjoy travelling and good design.",
        "This ceramic mug keeps coffee hot through long work sessions. Its "
        "travel-friendly shape fits a desk or a train table without spills. "
        "The minimalist design suits remote workers who value calm, durable gear.",
        "medium"),
    BenchmarkCase(
        "Summarise the main pros and cons of remote work for a small startup "
        "team, covering hiring, cost, culture, communication and management "
        "overheads in a short memo.",
        "Remote work widens the hiring pool and cuts office cost for a startup. "
        "The trade-offs are weaker culture, slower communication and harder "
        "management of distributed staff. Teams offset this with rituals, "
        "documentation and regular in-person meetups.",
        "medium"),
    BenchmarkCase(
        "Explain how browser caching works, with a concrete example, for a "
        "junior developer who is fixing a stale page issue.",
        "The browser stores copies of files like images and scripts after the "
        "first visit. On later visits it reuses those copies instead of "
        "downloading them again, which is faster. A stale page usually means "
        "the cached copy is old, so hard-refreshing or versioning the file "
        "forces a fresh download.",
        "medium"),
    BenchmarkCase(
        "Draft a polite email to a customer whose shipment is delayed by a "
        "week, apologising and offering a small discount.",
        "Dear customer, we are sorry your shipment is delayed by a week. The "
        "delay was caused by a warehouse backlog on our side. As an apology, "
        "here is a discount code for ten percent off your next order.",
        "medium"),
    BenchmarkCase(
        "Compare renting versus buying a home for a young couple in an "
        "expensive city, focusing on flexibility and long-term cost.",
        "Renting gives a young couple flexibility to move for work and avoids "
        "maintenance costs. Buying builds equity but ties up savings in a "
        "deposit and mortgage. In an expensive city the long-term cost "
        "depends on how long they stay, since buying wins over many years.",
        "medium"),
    BenchmarkCase(
        "Write a two-sentence social media post announcing a bakery's new "
        "sourdough loaf, in a warm and playful tone.",
        "Our new sourdough loaf is out of the oven and ready for its fans. "
        "Crusty, tangy and still warm, it is the bakery's happiest bake yet. "
        "Come grab a loaf before the weekend rush clears the shelf.",
        "medium"),
    # --- complex reasoning ---
    BenchmarkCase(
        "Prove that the greedy interval-scheduling algorithm is optimal, "
        "derive its time complexity, and explain the exchange argument "
        "step by step.",
        "Sort the intervals by finish time and repeatedly pick the earliest "
        "finishing compatible interval. The exchange argument shows any "
        "optimal schedule can be transformed to include that first greedy "
        "choice without losing intervals. Repeating the exchange proves the "
        "greedy schedule is optimal. Sorting dominates the running time, so "
        "the complexity is O(n log n).",
        "complex"),
    BenchmarkCase(
        "Debug this Python traceback and refactor the function for clarity: "
        "``` def f(x): return [i*i for i in x if i%2] ``` Traceback: "
        "TypeError: unsupported operand, thrown when x contains strings.",
        "The traceback happens because the function squares every item, "
        "including strings mixed into the list. Refactor it to filter for "
        "numbers first and give the function a descriptive name. The "
        "refactored version validates input types and raises a clear error "
        "for unsupported operands. This separates validation from the "
        "computation and makes the debug trail obvious.",
        "complex"),
    BenchmarkCase(
        "Analyse the trade-offs between microservices and a monolith for a "
        "payments platform, covering service architecture, consistency, "
        "deployment and failure modes in depth, with a multi-step "
        "migration analysis and a final recommendation.",
        "A monolith keeps payments consistent and simple to deploy, but "
        "scales as one unit and fails as one unit. Microservices isolate "
        "failures and let teams deploy independently, at the cost of "
        "distributed consistency and operational complexity. A multi-step "
        "migration starts by extracting the ledger behind an interface. "
        "The recommendation is to begin monolithic and split only when "
        "failure isolation demands it.",
        "complex"),
    # --- short but hard: the classifier under-routes this one ---
    BenchmarkCase(
        "Why does quicksort degrade to O(n^2) on already sorted input?",
        "Quicksort degrades when the pivot choice repeatedly splits the "
        "array into very unbalanced partitions. On already sorted input a "
        "naive first-element pivot makes one partition empty every time. "
        "The recursion depth then grows linearly and the total work becomes "
        "quadratic, O(n^2), instead of O(n log n).",
        "hard-short"),
)

ANSWER_BOOK: dict[str, str] = {c.prompt: c.expected for c in CASES}
TRAFFIC: list[str] = [c.prompt for c in CASES]
