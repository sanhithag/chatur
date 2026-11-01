"""Pedagogically verified curriculum content generator for micro-lessons and diagnostic hints.
Provides subject-specific explanations across 5 learning styles (Simple, Detailed, Visual, Analogy, Worked Example)
and context-aware hints for CBSE Classes 6-10.
"""

from typing import Dict, List, Tuple


def get_concept_hints(concept_code: str, question_text: str = "") -> List[str]:
    """Generates concept-specific pedagogical hints for practice questions."""
    c = concept_code.lower()
    q = question_text.lower()

    if "eng_rc" in c or "reading" in c:
        if "date" in q or "name" in q or "specific" in q:
            return [
                "Consider whether you are searching for a specific factual detail (a name, number, or year) or grasping the main gist.",
                "Scanning involves rapidly sweeping across lines looking only for capitalized words, numbers, or dates without reading every word.",
            ]
        elif "tone" in q:
            return [
                "Consider whether the author is expressing personal feelings or reporting objective factual observations.",
                "Academic and scientific papers maintain a neutral, objective, and evidence-based tone.",
            ]
        elif "inference" in q:
            return [
                "An inference is not explicitly stated in the text; it is deduced from context clues.",
                "Look for logical consequences implied by the facts provided.",
            ]
        return [
            "Identify whether the question asks for factual detail, the central thesis, or contextual vocabulary.",
            "Eliminate choices that are too broad, too narrow, or unsupported by the text.",
        ]

    elif "math_lin" in c or "linear" in c:
        return [
            "A linear equation in two variables has the general form ax + by + c = 0.",
            "To test if a point (x, y) lies on the line, substitute the coordinates into the equation and verify if LHS = RHS.",
        ]

    elif "math_alg" in c or "algebra" in c:
        return [
            "Group like terms together (e.g. combine x terms and constant terms separately).",
            "Recall standard identities: (a + b)² = a² + 2ab + b² and (a² - b²) = (a - b)(a + b).",
        ]

    elif "math_fra" in c or "fraction" in c:
        return [
            "To add fractions with different denominators, first find the Lowest Common Multiple (LCM).",
            "To multiply fractions, multiply numerators together and denominators together, then simplify.",
        ]

    elif "sci_mot" in c or "kinematics" in c:
        return [
            "Identify the given parameters: initial speed (u), final speed (v), acceleration (a), time (t), or distance (s).",
            "Choose the appropriate kinematic equation: v = u + at, s = ut + 0.5at², or v² = u² + 2as.",
        ]

    elif "sci_uni" in c:
        return [
            "Uniform motion means covering equal distances in equal intervals of time.",
            "The distance-time graph for uniform motion is a straight inclined line; non-uniform motion produces a curve.",
        ]

    elif "sci_sdt" in c:
        return [
            "Recall the fundamental rate relation: Speed = Distance / Time.",
            "To convert km/h to m/s, multiply by 5/18 (since 1000m / 3600s = 5/18).",
        ]

    elif "sci_mea" in c or "unit" in c:
        return [
            "Identify the standard SI base unit: length is measured in metres (m), mass in kilograms (kg), and time in seconds (s).",
            "Check unit prefixes: 1 km = 1,000 m, 1 m = 100 cm, 1 cm = 10 mm.",
        ]

    elif "sci_lig" in c or "light" in c or "reflection" in c:
        return [
            "First Law of Reflection: Angle of incidence (i) equals Angle of reflection (r).",
            "For spherical mirrors, focal length is half the radius of curvature: f = R / 2.",
        ]

    elif "sst_chr" in c or "history" in c or "source" in c:
        return [
            "Primary sources are created during the time period being studied (e.g., original diaries, letters, inscriptions).",
            "Chronology arranges historical events sequentially from earliest to latest in time.",
        ]

    # Universal subject fallback
    return [
        "Re-read the question carefully and identify what specific concept is being evaluated.",
        "Eliminate answer choices that contradict the fundamental definitions.",
    ]


def get_concept_lesson_content(
    concept_code: str,
    concept_name: str,
    grade: int,
    subject_domain: str,
    lang: str = "en",
) -> Tuple[str, List[str], Dict[str, Dict[str, str]], Dict[str, any]]:
    """Generates subject-accurate micro-lessons across all 5 explanation styles."""
    c = concept_code.lower()

    if "eng_rc" in c or "reading" in c:
        subject_name = "English Language & Literature"
        key_terms = ["Scanning", "Skimming", "Inference", "Context Clues", "Objective Tone"]

        styles = {
            "simple": {
                "title": "Core Reading Strategies: Skimming vs. Scanning",
                "content": (
                    "Reading comprehension requires different reading speeds and techniques depending on your goal:\n\n"
                    "• Skimming: Rapid reading to quickly understand the general gist, main idea, or overall theme of a passage.\n"
                    "• Scanning: Looking rapidly for specific target information (such as a name, date, statistic, or key vocabulary word) without reading every sentence.\n"
                    "• Golden Rule: Use skimming when asked 'What is the central theme?' and use scanning when asked 'In which year did event X occur?'."
                ),
            },
            "detailed": {
                "title": "Analytical Comprehension & Textual Inference",
                "content": (
                    "Effective reading in Class 7 English involves three distinct cognitive levels:\n\n"
                    "1. Literal Understanding: Identifying facts explicitly stated in the text (who, what, when, where).\n"
                    "2. Inferential Analysis: Reading between the lines. An inference is a logical conclusion derived from evidence and context clues rather than direct declaration.\n"
                    "3. Critical Evaluation: Analyzing the author's tone, purpose, and credibility. Academic texts maintain an objective, evidence-based tone, while editorial texts may express bias or persuasive intent."
                ),
            },
            "visual": {
                "title": "Visual Framework: The Reading Funnel",
                "content": (
                    "Visualizing Reading Techniques:\n\n"
                    "👁️ The Scanning Radar:\n"
                    "  [ Passage Text ] ---> Eyes zigzag rapidly looking ONLY for capital letters, numbers, or quotes (Dates, Names, Places).\n\n"
                    "📖 The Skimming Filter:\n"
                    "  Read Title ---> First Sentence of each paragraph ---> Final concluding paragraph (Gives 80% of main idea in 20% of time).\n\n"
                    "🔍 Deep Critical Reading:\n"
                    "  Read sentence-by-sentence with pencil annotations for inference and rhetoric."
                ),
            },
            "analogy": {
                "title": "Everyday Analogy: The Supermarket Search",
                "content": (
                    "Think of reading strategies like going into a large supermarket:\n\n"
                    "• Scanning: Walking into the supermarket needing only a carton of milk. You don't inspect every shelf; your eyes search directly for the dairy sign and the milk bottle.\n"
                    "• Skimming: Browsing the aisle signs to see what kinds of products this grocery store carries in general.\n"
                    "• Close Reading: Reading the nutritional facts and ingredient list on the back of the cereal box before buying."
                ),
            },
            "worked_example": {
                "title": "Worked Practice Example",
                "content": (
                    "Passage Snippet:\n"
                    "\"On 15 August 1947, India attained independence after decades of struggle led by Mahatma Gandhi and numerous freedom fighters.\"\n\n"
                    "Question: In which year did India attain independence?\n"
                    "Strategy Applied:\n"
                    "• Do NOT read every word from the beginning.\n"
                    "• Scan immediately for 4-digit numbers (years).\n"
                    "• The eye catches '1947' instantly.\n"
                    "Conclusion: Using scanning took less than 2 seconds!"
                ),
            },
        }

        comprehension = {
            "question": "Which reading strategy should you use to identify the central argument of an editorial?",
            "options": ["Scanning", "Skimming", "Spell-checking", "Memorization"],
            "correct_index": 1,
            "explanation": "Skimming allows you to quickly grasp the overarching theme and central argument by focusing on topic sentences and conclusions.",
        }

    elif "math_lin" in c or "linear" in c:
        subject_name = "Mathematics"
        key_terms = ["Linear Equation", "Cartesian Plane", "Slope-Intercept", "Infinite Solutions", "LHS = RHS"]

        styles = {
            "simple": {
                "title": "Linear Equations in Two Variables: Core Concept",
                "content": (
                    "A linear equation in two variables has the general form ax + by + c = 0, where a, b, and c are real numbers, and a and b are not both zero.\n\n"
                    "• What does 'linear' mean? When plotted on a Cartesian coordinate plane, every linear equation produces a perfectly straight line.\n"
                    "• Solutions: A single linear equation in two variables has infinitely many solutions, with each solution (x, y) representing a point on the line."
                ),
            },
            "detailed": {
                "title": "Algebraic Solutions & Graphical Representation",
                "content": (
                    "Detailed Analysis of ax + by + c = 0:\n\n"
                    "1. Finding Ordered Pairs: To graph the equation, assign arbitrary values to x and solve for y (or vice-versa) to find at least two coordinate pairs (x₁, y₁) and (x₂, y₂).\n"
                    "2. Special Cases:\n"
                    "   • x = k represents a vertical line parallel to the y-axis at distance k.\n"
                    "   • y = k represents a horizontal line parallel to the x-axis at distance k.\n"
                    "   • y = mx passes through the origin (0, 0)."
                ),
            },
            "visual": {
                "title": "Graphing the Straight Line on the Cartesian Plane",
                "content": (
                    "Visual Layout of 2x + y = 6:\n\n"
                    "📍 Intercepts:\n"
                    "  • If x = 0: 2(0) + y = 6 => y = 6 (y-intercept at (0, 6))\n"
                    "  • If y = 0: 2x + 0 = 6 => x = 3 (x-intercept at (3, 0))\n\n"
                    "📈 Connecting (0, 6) and (3, 0) with a ruler forms the straight line graph of all infinite solutions."
                ),
            },
            "analogy": {
                "title": "Real-World Analogy: The Cricket Score Equation",
                "content": (
                    "Imagine a batsman scoring total 50 runs consisting only of 4s and 6s:\n\n"
                    "• Equation: 4x + 6y = 50 (where x = number of fours, y = number of sixes).\n"
                    "• As the number of sixes increases, the required number of fours changes proportionally.\n"
                    "• Every valid combination of (x, y) that totals 50 is a solution point on the line!"
                ),
            },
            "worked_example": {
                "title": "Step-by-Step Problem Solving",
                "content": (
                    "Problem: If (2, 3) is a solution of the equation 3x + 2y = k, find the value of k.\n\n"
                    "Step 1: Substitute the given coordinates into the equation:\n"
                    "  x = 2, y = 3\n"
                    "Step 2: Compute LHS:\n"
                    "  3(2) + 2(3) = 6 + 6 = 12\n"
                    "Step 3: Equate LHS = RHS:\n"
                    "  k = 12.\n"
                    "Final Answer: The value of k is 12."
                ),
            },
        }

        comprehension = {
            "question": "How many solutions does the linear equation 3x + 5y = 15 have?",
            "options": ["Unique solution", "Two solutions", "Infinitely many solutions", "No solution"],
            "correct_index": 2,
            "explanation": "Any single linear equation in two variables has infinitely many solutions, each corresponding to a point on its straight line graph.",
        }

    elif "math_alg" in c or "algebra" in c:
        subject_name = "Mathematics"
        key_terms = ["Monomial", "Binomial", "Polynomial", "Like Terms", "Identity"]

        styles = {
            "simple": {
                "title": "Algebraic Expressions & Identities",
                "content": (
                    "An algebraic expression is formed by combining variables (unknowns like x, y) and constants with arithmetic operations (+, -, *, /).\n\n"
                    "• Like Terms: Terms having identical algebraic factors (e.g., 3x and 5x) can be added or subtracted.\n"
                    "• Unlike Terms: Terms with different variables or powers (e.g., 3x and 3y, or 2x and 2x²) cannot be combined."
                ),
            },
            "detailed": {
                "title": "Standard Algebraic Identities",
                "content": (
                    "An identity is an algebraic equality that holds true for all values of the variables.\n\n"
                    "Standard Identities:\n"
                    "1. (a + b)² = a² + 2ab + b²\n"
                    "2. (a - b)² = a² - 2ab + b²\n"
                    "3. a² - b² = (a + b)(a - b)\n"
                    "4. (x + a)(x + b) = x² + (a + b)x + ab"
                ),
            },
            "visual": {
                "title": "Geometric Proof of (a + b)²",
                "content": (
                    "Visualize a square with side length (a + b):\n\n"
                    "Divided into 4 smaller regions:\n"
                    "  • Large square: area a * a = a²\n"
                    "  • Small square: area b * b = b²\n"
                    "  • Two rectangles: area a * b = ab each\n\n"
                    "Total Area = a² + ab + ab + b² = a² + 2ab + b²."
                ),
            },
            "analogy": {
                "title": "Analogy: Apples and Oranges",
                "content": (
                    "Think of variables as different fruits:\n\n"
                    "• 3 apples (3x) + 2 apples (2x) = 5 apples (5x).\n"
                    "• But 3 apples (3x) + 2 oranges (2y) cannot become 5 'apple-oranges'! They remain 3x + 2y."
                ),
            },
            "worked_example": {
                "title": "Factorization Example",
                "content": (
                    "Problem: Factorize x² - 16.\n\n"
                    "Step 1: Recognize the difference of squares identity: a² - b² = (a + b)(a - b).\n"
                    "Step 2: Express 16 as a square: 16 = 4².\n"
                    "Step 3: Apply identity: x² - 4² = (x + 4)(x - 4).\n"
                    "Final Answer: (x + 4)(x - 4)."
                ),
            },
        }

        comprehension = {
            "question": "What is the simplified form of (2x + 3)(2x - 3)?",
            "options": ["4x² - 9", "4x² + 9", "4x² - 6x - 9", "2x² - 9"],
            "correct_index": 0,
            "explanation": "Using identity (a + b)(a - b) = a² - b², (2x)² - (3)² = 4x² - 9.",
        }

    elif "math_fra" in c or "fraction" in c or "decimal" in c:
        subject_name = "Mathematics"
        key_terms = ["Numerator", "Denominator", "Proper Fraction", "Improper Fraction", "LCM", "Equivalent Fractions"]
        styles = {
            "simple": {
                "title": "Understanding Fractions and Decimals",
                "content": (
                    "A fraction represents a part of a whole (written as a/b where b ≠ 0).\n\n"
                    "• Numerator (a): Number of equal parts taken.\n"
                    "• Denominator (b): Total number of equal parts into which the whole is divided.\n"
                    "• Adding unlike fractions: Convert them to equivalent fractions with a common denominator using the LCM."
                ),
            },
            "detailed": {
                "title": "Operations on Fractions & Decimal Conversion",
                "content": (
                    "Rules for Fraction Arithmetic:\n\n"
                    "1. Addition/Subtraction: a/b + c/d = (a·d + b·c) / (b·d).\n"
                    "2. Multiplication: (a/b) × (c/d) = (a × c) / (b × d).\n"
                    "3. Division: (a/b) ÷ (c/d) = (a/b) × (d/c) (multiply by the reciprocal).\n"
                    "4. Decimals: Fractions with denominators of 10, 100, 1000 can be written directly as decimals (e.g. 7/10 = 0.7, 3/100 = 0.03)."
                ),
            },
            "visual": {
                "title": "Visual Representation: The Pizza Model",
                "content": (
                    "Visualizing Fractions:\n\n"
                    "🍕 A whole pizza sliced into 8 equal slices:\n"
                    "  • Eating 2 slices = 2/8 = 1/4 of the pizza.\n"
                    "  • Eating 4 slices = 4/8 = 1/2 of the pizza.\n"
                    "  • Adding 1/4 + 1/2 = 2/8 + 4/8 = 6/8 = 3/4 of the pizza."
                ),
            },
            "analogy": {
                "title": "Everyday Analogy: Pocket Money Shares",
                "content": (
                    "Think of fractions as splitting a ₹100 note:\n\n"
                    "• Half (1/2) is ₹50.\n"
                    "• One-fourth (1/4) is ₹25.\n"
                    "• Three-fourths (3/4) is ₹75 (or 0.75 in decimal terms).\n"
                    "• Just like you can't add 2 ten-rupee notes and 3 twenty-rupee notes into '5 identical things' without counting rupees, you can't add fractions without a common denominator!"
                ),
            },
            "worked_example": {
                "title": "Addition of Unlike Fractions",
                "content": (
                    "Problem: Calculate 2/3 + 1/4.\n\n"
                    "Step 1: Find LCM of denominators 3 and 4: LCM(3, 4) = 12.\n"
                    "Step 2: Convert to equivalent fractions with denominator 12:\n"
                    "  2/3 = (2 × 4) / (3 × 4) = 8/12\n"
                    "  1/4 = (1 × 3) / (4 × 3) = 3/12\n"
                    "Step 3: Add numerators: 8/12 + 3/12 = 11/12.\n"
                    "Final Answer: 11/12."
                ),
            },
        }
        comprehension = {
            "question": "What is the result of 3/5 + 1/2?",
            "options": ["4/7", "11/10", "4/10", "6/10"],
            "correct_index": 1,
            "explanation": "LCM(5, 2) = 10. 3/5 = 6/10 and 1/2 = 5/10. 6/10 + 5/10 = 11/10 (or 1.1).",
        }

    elif "sci_mea" in c or "measurement" in c:
        subject_name = "Science (Physics)"
        key_terms = ["SI Base Units", "Metre", "Kilogram", "Second", "Unit Prefix", "Conversion Factor"]
        styles = {
            "simple": {
                "title": "Standard Units of Measurement",
                "content": (
                    "Measurement is the comparison of an unknown quantity with a known fixed quantity called a unit.\n\n"
                    "• International System of Units (SI Units):\n"
                    "  - Length: Metre (m)\n"
                    "  - Mass: Kilogram (kg)\n"
                    "  - Time: Second (s)\n"
                    "• Standard units ensure consistency across scientists and engineers worldwide."
                ),
            },
            "detailed": {
                "title": "Prefixes and Metric Conversion",
                "content": (
                    "Metric prefixes scale base units by powers of 10:\n\n"
                    "• Kilo (k) = 1,000 = 10³ (e.g., 1 km = 1,000 m)\n"
                    "• Centi (c) = 1/100 = 10⁻² (e.g., 1 m = 100 cm)\n"
                    "• Milli (m) = 1/1,000 = 10⁻³ (e.g., 1 m = 1,000 mm)\n"
                    "To convert from larger unit to smaller unit: Multiply.\n"
                    "To convert from smaller unit to larger unit: Divide."
                ),
            },
            "visual": {
                "title": "Visual Metric Ladder",
                "content": (
                    "Metric Conversion Ladder:\n\n"
                    "  Kilometre (km)  [×1000] ↓  [÷1000] ↑\n"
                    "  Metre (m)       [×100]  ↓  [÷100]  ↑\n"
                    "  Centimetre (cm) [×10]   ↓  [÷10]   ↑\n"
                    "  Millimetre (mm)"
                ),
            },
            "analogy": {
                "title": "Analogy: Ancient Handspans vs. Rulers",
                "content": (
                    "In ancient times, people measured cloth using their forearm ('cubit') or handspan:\n\n"
                    "• Problem: A tall shopkeeper's handspan is bigger than a short customer's handspan! Trading led to constant disputes.\n"
                    "• Solution: Standard SI units provide an unchangeable reference length that is exactly the same everywhere."
                ),
            },
            "worked_example": {
                "title": "Unit Conversion Calculation",
                "content": (
                    "Problem: Convert 4.5 kilometres into metres.\n\n"
                    "Step 1: Identify relation: 1 km = 1,000 m.\n"
                    "Step 2: Multiply 4.5 by 1,000:\n"
                    "  4.5 × 1,000 = 4,500 m.\n"
                    "Final Answer: 4,500 metres."
                ),
            },
        }
        comprehension = {
            "question": "What is the standard SI base unit of length?",
            "options": ["Centimetre", "Metre", "Kilometre", "Foot"],
            "correct_index": 1,
            "explanation": "The International System of Units (SI) defines the metre (m) as the base unit for length.",
        }

    elif "sci_sdt" in c:
        subject_name = "Science (Physics)"
        key_terms = ["Speed", "Distance", "Time", "Scalar Quantity", "SI Unit (m/s)", "Odometer", "Speedometer"]
        styles = {
            "simple": {
                "title": "Speed, Distance, and Time",
                "content": (
                    "Speed is defined as the distance travelled by an object per unit of time.\n\n"
                    "• Formula: Speed = Distance / Time\n"
                    "• SI Unit: Metre per second (m/s), though km/h is common for road vehicles.\n"
                    "• Higher speed means covering more distance in the same time."
                ),
            },
            "detailed": {
                "title": "Unit Conversion & Average Speed",
                "content": (
                    "Speed Computations:\n\n"
                    "1. Converting km/h to m/s: Multiply by 5/18 (1 km/h = 1000m / 3600s = 5/18 m/s).\n"
                    "2. Converting m/s to km/h: Multiply by 18/5.\n"
                    "3. Average Speed = Total Distance Travelled / Total Time Taken."
                ),
            },
            "visual": {
                "title": "The Speed Triangle",
                "content": (
                    "The Formula Triangle:\n\n"
                    "         /  D  \\\n"
                    "        /-------\\\n"
                    "       / S  | T  \\\n\n"
                    "• Cover D: Distance = Speed × Time\n"
                    "• Cover S: Speed = Distance / Time\n"
                    "• Cover T: Time = Distance / Speed"
                ),
            },
            "analogy": {
                "title": "Analogy: Road Trip to the Next City",
                "content": (
                    "Imagine driving from Bangalore to Mysore (150 km) taking 3 hours:\n\n"
                    "• Speedometer: Reads 80 km/h on highway stretches and 20 km/h at toll gates (Instantaneous speed).\n"
                    "• Total Trip: 150 km / 3 hours = 50 km/h (Average speed for the whole journey)."
                ),
            },
            "worked_example": {
                "title": "Speed Conversion & Distance Problem",
                "content": (
                    "Problem: A train runs at a speed of 54 km/h. How many metres does it travel in 20 seconds?\n\n"
                    "Step 1: Convert speed to m/s:\n"
                    "  Speed = 54 × (5/18) = 3 × 5 = 15 m/s.\n"
                    "Step 2: Distance = Speed × Time:\n"
                    "  Distance = 15 m/s × 20 s = 300 metres.\n"
                    "Final Answer: The train travels 300 metres."
                ),
            },
        }
        comprehension = {
            "question": "A runner covers 200 metres in 25 seconds. What is their speed in m/s?",
            "options": ["6 m/s", "8 m/s", "10 m/s", "12 m/s"],
            "correct_index": 1,
            "explanation": "Speed = Distance / Time = 200 m / 25 s = 8 m/s.",
        }

    elif "sci_uni" in c:
        subject_name = "Science (Physics)"
        key_terms = ["Uniform Motion", "Non-Uniform Motion", "Distance-Time Graph", "Constant Speed", "Acceleration"]
        styles = {
            "simple": {
                "title": "Uniform vs. Non-Uniform Motion",
                "content": (
                    "Objects in motion can travel at a steady rate or at variable rates:\n\n"
                    "• Uniform Motion: An object covers equal distances in equal intervals of time.\n"
                    "• Non-Uniform Motion: An object covers unequal distances in equal intervals of time (speed changes)."
                ),
            },
            "detailed": {
                "title": "Graphical Analysis of Motion",
                "content": (
                    "Interpreting Distance-Time Graphs (s-t):\n\n"
                    "1. Straight Inclined Line: Represents Uniform Motion. The slope equals the constant speed (v = Δs / Δt).\n"
                    "2. Curved Line: Represents Non-Uniform Motion (acceleration or deceleration).\n"
                    "3. Horizontal Line: The object is at rest (speed = 0)."
                ),
            },
            "visual": {
                "title": "Distance-Time Graphs Compared",
                "content": (
                    "Graph Comparison:\n\n"
                    "Distance (m)                      Distance (m)\n"
                    "   ^     / (Uniform)                 ^       / (Non-Uniform)\n"
                    "   |    /                            |     /'\n"
                    "   |   /                             |   /'\n"
                    "   |  /                              |  /\n"
                    "   | /                               | /'\n"
                    "   +---------> Time (s)              +---------> Time (s)\n"
                    "    Straight Line                      Curved Line"
                ),
            },
            "analogy": {
                "title": "Analogy: Highway Cruise Control vs City Traffic",
                "content": (
                    "Think of car rides:\n\n"
                    "• Cruise control on an empty expressway: Steady 80 km/h covering equal distance every minute -> Uniform motion.\n"
                    "• Driving in city traffic: Stop and go at traffic lights -> Non-uniform motion."
                ),
            },
            "worked_example": {
                "title": "Identifying Motion Type from Data",
                "content": (
                    "Problem: An object covers 10m in 1st second, 10m in 2nd second, and 10m in 3rd second. Classify its motion.\n\n"
                    "Step 1: Check distance intervals: Δs₁ = 10m, Δs₂ = 10m, Δs₃ = 10m.\n"
                    "Step 2: Time intervals are all equal (1 second).\n"
                    "Step 3: Since it covers equal distances in equal time intervals, the speed is constant (10 m/s).\n"
                    "Final Answer: The motion is Uniform Motion."
                ),
            },
        }
        comprehension = {
            "question": "What does a straight inclined line on a distance-time graph represent?",
            "options": ["Object at rest", "Uniform motion with constant speed", "Accelerated non-uniform motion", "Infinite speed"],
            "correct_index": 1,
            "explanation": "A straight inclined line indicates that distance increases proportionally with time, which defines uniform motion at constant speed.",
        }

    elif "sci_lig" in c or "light" in c or "reflection" in c:
        subject_name = "Science (Physics)"
        key_terms = ["Reflection", "Angle of Incidence", "Angle of Reflection", "Normal", "Convex Mirror", "Focal Length"]

        styles = {
            "simple": {
                "title": "Laws of Light Reflection",
                "content": (
                    "Light travels in straight lines. When light strikes a polished surface (like a mirror), it bounces back into the same medium—this phenomenon is called reflection.\n\n"
                    "• First Law: The angle of incidence equals the angle of reflection (∠i = ∠r).\n"
                    "• Second Law: The incident ray, the reflected ray, and the normal to the mirror at the point of incidence all lie in the same plane."
                ),
            },
            "detailed": {
                "title": "Spherical Mirrors & Ray Diagrams",
                "content": (
                    "Curved mirrors have a center of curvature (C), pole (P), and principal focus (F):\n\n"
                    "• Concave Mirror: Reflecting surface curves inward. Focuses parallel light rays to a real focus. Used by dentists, in torches and solar furnaces.\n"
                    "• Convex Mirror: Reflecting surface curves outward. Diverges rays. Always produces erect, virtual, diminished images with a wider field of view. Used as rear-view mirrors in vehicles."
                ),
            },
            "visual": {
                "title": "Ray Diagram: Angle of Incidence and Reflection",
                "content": (
                    "Ray Diagram:\n\n"
                    "       Incident Ray \\      | Normal      / Reflected Ray\n"
                    "                    \\     |            /\n"
                    "                     \\ ∠i | ∠r        /\n"
                    "        ==============\\===|==========/============== Mirror\n"
                    "                         Point of Incidence (O)\n"
                    "∠i = ∠r (Both measured strictly with respect to the perpendicular normal)."
                ),
            },
            "analogy": {
                "title": "Analogy: Bouncing a Tennis Ball Against a Wall",
                "content": (
                    "Think of light rays like a tennis ball thrown against a smooth brick wall:\n\n"
                    "• If you throw the ball straight on (perpendicular, normal), it bounces straight back.\n"
                    "• If you throw it at an angle of 30° to the perpendicular, it bounces off at exactly 30° on the other side!"
                ),
            },
            "worked_example": {
                "title": "Focal Length Calculation",
                "content": (
                    "Problem: Find the focal length of a convex mirror whose radius of curvature is 32 cm.\n\n"
                    "Step 1: Formula relating focal length f and radius of curvature R: f = R / 2.\n"
                    "Step 2: Substitute R = 32 cm:\n"
                    "  f = 32 / 2 = 16 cm.\n"
                    "Final Answer: The focal length of the mirror is +16 cm."
                ),
            },
        }

        comprehension = {
            "question": "If a ray of light strikes a plane mirror at an angle of incidence of 35°, what is the angle of reflection?",
            "options": ["35°", "55°", "70°", "90°"],
            "correct_index": 0,
            "explanation": "According to the first law of reflection, the angle of reflection is always exactly equal to the angle of incidence (35°).",
        }

    elif "sst_chr" in c or "history" in c or "source" in c:
        subject_name = "Social Science (History)"
        key_terms = ["Primary Source", "Secondary Source", "Chronology", "Corroboration", "Historical Evidence"]

        styles = {
            "simple": {
                "title": "Historical Inquiry: Chronology & Sources",
                "content": (
                    "History is not mere memorization of dates; it is the evidence-based study of change over time.\n\n"
                    "• Chronology: Placing events in their true sequential order of occurrence. This reveals cause-and-effect relationships.\n"
                    "• Sources: Historians rely on evidence to reconstruct past realities."
                ),
            },
            "detailed": {
                "title": "Primary vs. Secondary Sources",
                "content": (
                    "Categorizing Historical Sources:\n\n"
                    "1. Primary Sources: Artifacts, documents, letters, diaries, coins, or oral testimonies created contemporaneously during the period of study.\n"
                    "2. Secondary Sources: Works written after the event by scholars, historians, or authors who analyze and interpret primary data (e.g. textbooks, modern documentaries).\n"
                    "3. Critical Inquiry: Historians cross-reference multiple accounts to identify bias and determine historical authenticity."
                ),
            },
            "visual": {
                "title": "Visual Timeline of the Indian National Movement",
                "content": (
                    "Sequential Timeline:\n\n"
                    "  1857: First War of Independence\n"
                    "    ↓\n"
                    "  1885: Formation of Indian National Congress (INC)\n"
                    "    ↓\n"
                    "  1919: Rowlatt Act & Jallianwala Bagh Massacre\n"
                    "    ↓\n"
                    "  1920: Non-Cooperation Movement launched by Mahatma Gandhi\n"
                    "    ↓\n"
                    "  1930: Dandi March & Civil Disobedience Movement\n"
                    "    ↓\n"
                    "  1942: Quit India Movement\n"
                    "    ↓\n"
                    "  1947: Independence of India."
                ),
            },
            "analogy": {
                "title": "Analogy: A Crime Scene Detective",
                "content": (
                    "Think of an inquiry like a detective investigating a case:\n\n"
                    "• Primary Source: The eyewitness testimony of someone present at the scene, or footprints and security camera footage.\n"
                    "• Secondary Source: The newspaper report written the next morning summarizing what the police told reporters."
                ),
            },
            "worked_example": {
                "title": "Source Classification Practice",
                "content": (
                    "Problem: Classify the following item:\n"
                    "\"The original personal diary kept by Anne Frank while in hiding between 1942 and 1944.\"\n\n"
                    "Analysis:\n"
                    "• Was it created during the event? Yes (1942-1944).\n"
                    "• Was it written by a firsthand participant? Yes.\n"
                    "Conclusion: It is a Primary Historical Source."
                ),
            },
        }

        comprehension = {
            "question": "Which of the following is a primary source of history?",
            "options": ["A modern history textbook written in 2024", "An original copper-plate inscription from the Chola Dynasty", "A YouTube animated summary", "A fictional movie set in the Mughal era"],
            "correct_index": 1,
            "explanation": "An original copper-plate inscription was produced during the Chola era by contemporary artisans, making it direct primary evidence.",
        }

    else:
        # Default Science: Motion / Physics
        subject_name = "Science (Physics)"
        key_terms = ["SI Units", "Uniform Motion", "Velocity-Time Slope", "Displacement", "Acceleration"]

        styles = {
            "simple": {
                "title": f"Core Principle: {concept_name}",
                "content": (
                    f"Welcome to this micro-lesson on {concept_name}.\n\n"
                    f"• Fundamental Definition: In Class {grade} Physics, motion describes change in position over time relative to a reference frame.\n"
                    f"• Standard Units: Speed and velocity are measured in metres per second (m/s). Distance is measured in metres (m).\n"
                    f"• Rate of Change: Speed is scalar (distance/time), while velocity is vector (displacement/time)."
                ),
            },
            "detailed": {
                "title": f"Mathematical Formulation of {concept_name}",
                "content": (
                    "Kinematics of Uniformly Accelerated Rectilinear Motion:\n\n"
                    "1. v = u + at\n"
                    "2. s = ut + 0.5 at²\n"
                    "3. v² = u² + 2as\n\n"
                    "Where u = initial velocity, v = final velocity, a = constant acceleration, t = time elapsed, s = displacement."
                ),
            },
            "visual": {
                "title": "Graphical Derivation of Equations of Motion",
                "content": (
                    "Velocity-Time Graph (v-t):\n\n"
                    "• Slope = (v - u) / t = Acceleration (a)\n"
                    "• Area under curve = Area of Rectangle (u * t) + Area of Triangle (0.5 * (v - u) * t) = ut + 0.5 at² = Displacement (s)."
                ),
            },
            "analogy": {
                "title": "Everyday Analogy: The Metro Train",
                "content": (
                    "Imagine riding the Metro train:\n\n"
                    "• Pulling away from station: Velocity increases from 0 m/s to 20 m/s in 10 seconds -> Acceleration = +2 m/s².\n"
                    "• Cruising between stations: Steady speed covering 20 metres every single second -> Uniform motion.\n"
                    "• Braking before destination: Negative acceleration (retardation) brings train safely to rest."
                ),
            },
            "worked_example": {
                "title": "Worked Kinematics Calculation",
                "content": (
                    "Problem: A car accelerates from rest at 2 m/s² for 5 seconds. Find its final velocity and distance covered.\n\n"
                    "Step 1: Given u = 0, a = 2 m/s², t = 5s.\n"
                    "Step 2: v = u + at = 0 + (2 * 5) = 10 m/s.\n"
                    "Step 3: s = ut + 0.5 at² = 0 + 0.5 * 2 * (25) = 25 metres.\n"
                    "Final Answer: Final velocity is 10 m/s and distance is 25 m."
                ),
            },
        }

        comprehension = {
            "question": f"Which equation of motion gives position as a function of time?",
            "options": ["v = u + at", "s = ut + 0.5at²", "v² = u² + 2as", "p = mv"],
            "correct_index": 1,
            "explanation": "s = ut + 0.5at² explicitly relates position/displacement (s) to elapsed time (t).",
        }

    return subject_name, key_terms, styles, comprehension
