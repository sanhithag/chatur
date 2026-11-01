import asyncio
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, async_session_factory, engine
from app.models.assessment import (
    LevelChangeProposal,
    Question,
    StudentMastery,
)
from app.models.curriculum import (
    Board,
    Concept,
    ConceptPrerequisite,
    CurriculumChapter,
    CurriculumSubject,
    CurriculumTopic,
    CurriculumUnit,
)
from app.models.student import (
    ClassSection,
    ParentChildLink,
    StudentEnrollment,
    StudentProfile,
    TeacherAssignment,
)
from app.models.user import School, UserAccount
from app.services.auth import get_password_hash


async def seed_database():
    print("Beginning CHATUR database seed...")

    # Ensure tables are created
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # Check if already seeded
        check_user = await session.execute(
            select(UserAccount).where(UserAccount.username == "superadmin")
        )
        if check_user.scalar_one_or_none():
            print("Database appears to already be seeded. Skipping duplicate seeding.")
            return

        now = datetime.now(timezone.utc)

        # 1. Board
        board = Board(
            code="CBSE",
            name="Central Board of Secondary Education",
            is_active=True,
        )
        session.add(board)
        await session.flush()
        print(f"Created Board: {board.code}")

        # 2. School
        school = School(
            name="CHATUR Demo School",
            code="CHATUR-DEMO",
            is_active=True,
        )
        session.add(school)
        await session.flush()
        print(f"Created School: {school.name} ({school.code})")

        # 3. Users
        # Super Admin
        super_admin = UserAccount(
            school_id=None,
            role="super_admin",
            username="superadmin",
            name="System Superadmin",
            email="admin@chatur.school",
            password_hash=get_password_hash("Admin@CHATUR2024"),
            preferred_lang="en",
            is_active=True,
        )
        session.add(super_admin)

        # School Admin
        school_admin = UserAccount(
            school_id=school.id,
            role="admin",
            username="admin",
            name="Principal Ramesh Kumar",
            email="schooladmin@chatur.school",
            password_hash=get_password_hash("Admin@School2024"),
            preferred_lang="en",
            is_active=True,
        )
        session.add(school_admin)

        # Teacher
        teacher = UserAccount(
            school_id=school.id,
            role="teacher",
            username="teacher1",
            name="Priya Sharma",
            email="priya.sharma@chatur.school",
            phone="+919876543210",
            password_hash=get_password_hash("Teacher@2024"),
            preferred_lang="en",
            is_active=True,
        )
        session.add(teacher)

        # Students (1..5)
        students_info = [
            ("student1", "Aarav Patel", "aarav@student.chatur.school", 9, "A", "01", 340, 5),
            ("student2", "Diya Reddy", "diya@student.chatur.school", 9, "A", "02", 280, 3),
            ("student3", "Rohan Gupta", "rohan@student.chatur.school", 9, "A", "03", 420, 8),
            ("student4", "Ananya Singh", "ananya@student.chatur.school", 9, "A", "04", 190, 2),
            ("student5", "Vikram Verma", "vikram@student.chatur.school", 9, "A", "05", 310, 4),
        ]

        student_accounts = []
        student_profiles = []

        for username, name, email, grade, sec, roll, xp, streak in students_info:
            user = UserAccount(
                school_id=school.id,
                role="student",
                username=username,
                name=name,
                email=email,
                password_hash=get_password_hash("Student@2024"),
                preferred_lang="en",
                is_active=True,
            )
            session.add(user)
            await session.flush()
            student_accounts.append(user)

            profile = StudentProfile(
                user_id=user.id,
                school_id=school.id,
                grade=grade,
                section=sec,
                roll_no=roll,
                total_xp=xp,
                current_streak=streak,
                longest_streak=streak + 2,
                last_active_at=now,
            )
            session.add(profile)
            await session.flush()
            student_profiles.append(profile)

        # Parent
        parent = UserAccount(
            school_id=school.id,
            role="parent",
            username="parent1",
            name="Suresh Patel",
            email="parent1@gmail.com",
            phone="+919876543211",
            password_hash=get_password_hash("Parent@2024"),
            preferred_lang="en",
            is_active=True,
        )
        session.add(parent)
        await session.flush()

        # 4. Class Section: Grade 9, Section A
        section_9a = ClassSection(
            school_id=school.id,
            academic_year="2026-27",
            grade=9,
            section="A",
            is_active=True,
        )
        session.add(section_9a)
        await session.flush()
        print(f"Created ClassSection: Grade {section_9a.grade}-{section_9a.section}")

        # Enroll all 5 students into Grade 9A
        for sp in student_profiles:
            enrollment = StudentEnrollment(
                student_id=sp.id,
                section_id=section_9a.id,
                is_active=True,
            )
            session.add(enrollment)

        # Parent-Child Link (parent1 -> student1)
        parent_link = ParentChildLink(
            parent_user_id=parent.id,
            student_id=student_profiles[0].id,
            relation_type="father",
            consent_given=True,
            consent_at=now,
        )
        session.add(parent_link)

        # 5. Curriculum Subjects
        subjects_data = [
            ("MATH", "Mathematics", "గణితం", "गणित", "mathematics", 1),
            ("SCI", "Science", "సైన్స్", "विज्ञान", "science", 2),
            ("ENG", "English Language & Literature", "ఇంగ్లీష్", "अंग्रेज़ी", "english", 3),
            ("HIN", "Hindi", "హిందీ", "हिंदी", "hindi", 4),
            ("SST", "Social Science", "సాంఘిక శాస్త్రం", "सामाजिक विज्ञान", "social_science", 5),
            ("CS", "Computer Science", "కంప్యూటర్ సైన్స్", "कंप्यूटर साइंस", "computer", 6),
        ]

        subject_map = {}
        for code, name_en, name_te, name_hi, domain, sort_order in subjects_data:
            subj = CurriculumSubject(
                board_id=board.id,
                code=code,
                name_en=name_en,
                name_te=name_te,
                name_hi=name_hi,
                domain=domain,
                is_active=True,
                sort_order=sort_order,
            )
            session.add(subj)
            await session.flush()
            subject_map[code] = subj

        # Teacher Assignment: teacher1 to Class 9A for Science and Mathematics
        ta_sci = TeacherAssignment(
            teacher_user_id=teacher.id,
            section_id=section_9a.id,
            subject_id=subject_map["SCI"].id,
            is_class_teacher=True,
        )
        session.add(ta_sci)

        ta_math = TeacherAssignment(
            teacher_user_id=teacher.id,
            section_id=section_9a.id,
            subject_id=subject_map["MATH"].id,
            is_class_teacher=False,
        )
        session.add(ta_math)

        # 6. Units, Chapters, Topics, and Concepts
        # Helper to create hierarchy
        async def create_hierarchy(subject_code, grade, unit_no, unit_name, ch_no, ch_name, topic_no, topic_name, concept_dict):
            subj = subject_map[subject_code]
            unit = CurriculumUnit(
                subject_id=subj.id,
                grade=grade,
                academic_year="2026-27",
                unit_no=unit_no,
                name_en=unit_name,
                source_ref=f"NCERT Class {grade} {subject_code}",
            )
            session.add(unit)
            await session.flush()

            chapter = CurriculumChapter(
                unit_id=unit.id,
                chapter_no=ch_no,
                name_en=ch_name,
                source_ref=f"NCERT Ch {ch_no}",
                ncert_verified=True,
            )
            session.add(chapter)
            await session.flush()

            topic = CurriculumTopic(
                chapter_id=chapter.id,
                topic_no=topic_no,
                name_en=topic_name,
            )
            session.add(topic)
            await session.flush()

            c = Concept(
                topic_id=topic.id,
                code=concept_dict["code"],
                name_en=concept_dict["name_en"],
                name_te=concept_dict.get("name_te"),
                name_hi=concept_dict.get("name_hi"),
                grade=grade,
                difficulty_band=concept_dict.get("difficulty_band", "medium"),
                learning_objectives=concept_dict.get("learning_objectives", []),
                common_misconceptions=concept_dict.get("common_misconceptions", []),
                content_status="approved",
                is_active=True,
                sort_order=concept_dict.get("sort_order", 1),
            )
            session.add(c)
            await session.flush()
            return c

        concept_records = {}

        # SCI Class 6: sci_mea6 'Measurement & Units'
        c_mea6 = await create_hierarchy(
            "SCI", 6, 1, "Physical Measurement", 1, "Motion and Measurement of Distances", 1, "Measurement & Standard Units",
            {
                "code": "sci_mea6",
                "name_en": "Measurement & Units",
                "name_te": "కొలతలు మరియు ప్రమాణాలు",
                "name_hi": "मापन और मात्रक",
                "difficulty_band": "easy",
                "learning_objectives": ["Understand standard units (SI)", "Convert metres, kilometres, and centimetres"],
                "common_misconceptions": [{"misconception": "Confusing mass with weight", "remediation": "Review definitions"}],
            }
        )
        concept_records["sci_mea6"] = c_mea6

        # SCI Class 7: sci_sdt7 'Speed, Distance and Time'
        c_sdt7 = await create_hierarchy(
            "SCI", 7, 1, "Motion and Time", 1, "Time and Motion", 1, "Speed Calculation",
            {
                "code": "sci_sdt7",
                "name_en": "Speed, Distance and Time",
                "name_te": "వేగం, దూరం మరియు సమయం",
                "name_hi": "चाल, दूरी और समय",
                "difficulty_band": "medium",
                "learning_objectives": ["Define speed as distance per unit time", "Calculate speed in m/s and km/h"],
                "common_misconceptions": [{"misconception": "Thinking faster speed always means greater distance covered regardless of time", "remediation": "Apply s = d/t formula"}],
            }
        )
        concept_records["sci_sdt7"] = c_sdt7

        # SCI Class 8: sci_uni8 'Uniform and Non-Uniform Motion'
        c_uni8 = await create_hierarchy(
            "SCI", 8, 1, "Force and Motion", 1, "Motion", 1, "Uniform vs Non-Uniform Motion",
            {
                "code": "sci_uni8",
                "name_en": "Uniform and Non-Uniform Motion",
                "name_te": "సమ మరియు అసమ చలనం",
                "name_hi": "एकसमान और असमान गति",
                "difficulty_band": "medium",
                "learning_objectives": ["Distinguish uniform and non-uniform motion", "Interpret distance-time graphs"],
            }
        )
        concept_records["sci_uni8"] = c_uni8

        # SCI Class 9: sci_mot9 'Equations of Motion'
        c_mot9 = await create_hierarchy(
            "SCI", 9, 1, "Motion, Force and Work", 1, "Motion", 1, "Kinematics Equations",
            {
                "code": "sci_mot9",
                "name_en": "Equations of Motion",
                "name_te": "చలన సమీకరణాలు",
                "name_hi": "गति के समीकरण",
                "difficulty_band": "hard",
                "learning_objectives": ["Derive v = u + at, s = ut + 0.5at^2, v^2 = u^2 + 2as", "Solve numerical kinematics problems"],
            }
        )
        concept_records["sci_mot9"] = c_mot9

        # MATH Class 6: math_fra6 'Fractions and Decimals'
        c_fra6 = await create_hierarchy(
            "MATH", 6, 1, "Number Operations", 1, "Fractions and Decimals", 1, "Fractional Arithmetic",
            {
                "code": "math_fra6",
                "name_en": "Fractions and Decimals",
                "name_te": "భిన్నాలు మరియు దశాంశాలు",
                "name_hi": "भिन्न और दशमलव",
                "difficulty_band": "easy",
                "learning_objectives": ["Add and multiply fractions", "Convert decimals to fractions"],
            }
        )
        concept_records["math_fra6"] = c_fra6

        # MATH Class 8: math_alg8 'Algebraic Expressions'
        c_alg8 = await create_hierarchy(
            "MATH", 8, 1, "Algebraic Foundations", 1, "Algebraic Expressions", 1, "Identities and Operations",
            {
                "code": "math_alg8",
                "name_en": "Algebraic Expressions",
                "name_te": "బీజీయ సమాసాలు",
                "name_hi": "बीजीय व्यंजक",
                "difficulty_band": "medium",
                "learning_objectives": ["Form algebraic expressions", "Apply standard algebraic identities"],
            }
        )
        concept_records["math_alg8"] = c_alg8

        # MATH Class 9: math_lin9 'Linear Equations in Two Variables'
        c_lin9 = await create_hierarchy(
            "MATH", 9, 1, "Linear Algebra", 1, "Linear Equations in Two Variables", 1, "Solutions and Graphs",
            {
                "code": "math_lin9",
                "name_en": "Linear Equations in Two Variables",
                "name_te": "రెండు చరరాశులలో సరళ సమీకరణాలు",
                "name_hi": "दो चरों वाले रैखिक समीकरण",
                "difficulty_band": "hard",
                "learning_objectives": ["Identify linear equations of form ax + by + c = 0", "Plot linear graphs on Cartesian plane"],
            }
        )
        concept_records["math_lin9"] = c_lin9

        # SCI Class 8: sci_lig8 'Light: Reflection and Refraction'
        c_lig8 = await create_hierarchy(
            "SCI", 8, 2, "Optics", 2, "Light: Reflection and Refraction", 1, "Reflection & Mirrors",
            {
                "code": "sci_lig8",
                "name_en": "Light: Reflection and Refraction",
                "name_te": "కాంతి: పరావర్తనం మరియు వక్రీభవనం",
                "name_hi": "प्रकाश: परावर्तन और अपवर्तन",
                "difficulty_band": "medium",
                "learning_objectives": ["State laws of reflection", "Understand image formation by spherical mirrors"],
            }
        )
        concept_records["sci_lig8"] = c_lig8

        # ENG Class 7: eng_rc7 'Reading Comprehension'
        c_rc7 = await create_hierarchy(
            "ENG", 7, 1, "Reading & Language", 1, "Reading Comprehension", 1, "Inference & Analysis",
            {
                "code": "eng_rc7",
                "name_en": "Reading Comprehension",
                "name_te": "రీడింగ్ కాంప్రహెన్షన్",
                "name_hi": "अपठित बोध",
                "difficulty_band": "medium",
                "learning_objectives": ["Identify central theme and tone", "Make factual and inferential conclusions"],
            }
        )
        concept_records["eng_rc7"] = c_rc7

        # SST Class 10: sst_chr10 'Chronology and Source Interpretation'
        c_chr10 = await create_hierarchy(
            "SST", 10, 1, "Historical Methodology", 1, "Historical Inquiry", 1, "Source Evaluation",
            {
                "code": "sst_chr10",
                "name_en": "Chronology and Source Interpretation",
                "name_te": "కాలక్రమం మరియు వనరుల వివరణ",
                "name_hi": "कालक्रम और स्रोत व्याख्या",
                "difficulty_band": "hard",
                "learning_objectives": ["Construct chronological timelines", "Differentiate primary and secondary historical evidence"],
            }
        )
        concept_records["sst_chr10"] = c_chr10

        # 7. Concept Prerequisites
        prereqs = [
            (c_sdt7.id, c_mea6.id, True, 1.0),
            (c_uni8.id, c_sdt7.id, True, 1.0),
            (c_mot9.id, c_uni8.id, True, 1.0),
            (c_alg8.id, c_fra6.id, True, 1.0),
            (c_lin9.id, c_alg8.id, True, 1.0),
            (c_lig8.id, c_mea6.id, False, 0.7),
        ]

        for cid, pid, is_strict, weight in prereqs:
            cp = ConceptPrerequisite(
                concept_id=cid,
                prerequisite_id=pid,
                is_strict=is_strict,
                weight=weight,
            )
            session.add(cp)

        await session.flush()
        print("Created Concept Prerequisites graph.")

        # 8. Questions (3-4 MCQ questions per concept, approved)
        questions_pool = [
            # sci_mea6
            (c_mea6.id, "What is the SI unit of length?", ["Kilometre", "Metre", "Centimetre", "Millimetre"], 1, "The SI base unit of length is the metre (m).", "remember", 0.3),
            (c_mea6.id, "How many centimetres are there in 2.5 metres?", ["25 cm", "250 cm", "2500 cm", "0.25 cm"], 1, "1 metre = 100 centimetres, so 2.5 * 100 = 250 cm.", "apply", 0.4),
            (c_mea6.id, "Which measuring tool is best suited for measuring the girth of a tree?", ["Metre scale", "Measuring tape", "Plastic ruler", "Vernier caliper"], 1, "A flexible measuring tape wraps easily around curved surfaces.", "understand", 0.4),

            # sci_sdt7
            (c_sdt7.id, "A bus covers 120 km in 3 hours. What is its average speed?", ["30 km/h", "35 km/h", "40 km/h", "45 km/h"], 2, "Speed = Distance / Time = 120 / 3 = 40 km/h.", "apply", 0.5),
            (c_sdt7.id, "Convert a speed of 18 km/h into m/s:", ["5 m/s", "10 m/s", "15 m/s", "20 m/s"], 0, "18 * (5/18) = 5 m/s.", "apply", 0.5),
            (c_sdt7.id, "What does the slope of a distance-time graph represent?", ["Acceleration", "Speed", "Force", "Displacement"], 1, "The slope (distance/time) represents the speed of the object.", "understand", 0.5),

            # sci_uni8
            (c_uni8.id, "An object moves with uniform motion when it covers:", ["Equal distances in unequal intervals of time", "Equal distances in equal intervals of time", "Unequal distances in equal intervals of time", "Zero distance in all time intervals"], 1, "Uniform motion implies covering equal distances in equal intervals of time.", "understand", 0.5),
            (c_uni8.id, "What shape is the distance-time graph for non-uniform motion?", ["A horizontal straight line", "A curved line", "A straight line sloped upward", "A vertical straight line"], 1, "Non-uniform motion gives a curved distance-time plot.", "understand", 0.6),
            (c_uni8.id, "A car travels 20 km in the 1st hour and 40 km in the 2nd hour. Its motion is:", ["Uniform", "Non-uniform", "Stationary", "Periodic"], 1, "Since speed changes across equal time intervals, it is non-uniform.", "apply", 0.5),

            # sci_mot9
            (c_mot9.id, "Which equation of motion gives the position-time relation?", ["v = u + at", "s = ut + 0.5at²", "v² = u² + 2as", "p = mv"], 1, "s = ut + 0.5at² relates position s and time t.", "remember", 0.6),
            (c_mot9.id, "A car starts from rest (u=0) with acceleration 2 m/s². What is its speed after 4 seconds?", ["4 m/s", "6 m/s", "8 m/s", "10 m/s"], 2, "v = u + at = 0 + (2 * 4) = 8 m/s.", "apply", 0.7),
            (c_mot9.id, "A ball is thrown upward with initial velocity 20 m/s (g=10 m/s²). Maximum height attained is:", ["10 m", "20 m", "30 m", "40 m"], 1, "v² = u² - 2gh => 0 = 400 - 20h => h = 20 m.", "analyze", 0.8),

            # math_fra6
            (c_fra6.id, "Simplify the sum: 3/4 + 1/2", ["4/6", "5/4", "1", "3/8"], 1, "3/4 + 2/4 = 5/4.", "apply", 0.3),
            (c_fra6.id, "What is 0.75 expressed as a common fraction in simplest terms?", ["7/10", "3/4", "15/20", "75/1000"], 1, "75/100 simplifies to 3/4.", "understand", 0.4),
            (c_fra6.id, "Multiply 2/3 by 9/4:", ["3/2", "18/7", "5/7", "18/24"], 0, "(2 * 9) / (3 * 4) = 18/12 = 3/2.", "apply", 0.4),

            # math_alg8
            (c_alg8.id, "What is the expansion of (a + b)²?", ["a² + b²", "a² + 2ab + b²", "a² - 2ab + b²", "2a + 2b"], 1, "Standard identity: (a + b)² = a² + 2ab + b².", "remember", 0.4),
            (c_alg8.id, "Subtract 3x - 4 from 5x + 2:", ["2x + 6", "2x - 6", "8x - 2", "2x + 2"], 0, "(5x + 2) - (3x - 4) = 2x + 6.", "apply", 0.5),
            (c_alg8.id, "Factorize: x² - 9", ["(x - 3)(x - 3)", "(x + 3)(x - 3)", "(x + 9)(x - 1)", "(x² - 3)"], 1, "Difference of squares: (x + 3)(x - 3).", "understand", 0.5),

            # math_lin9
            (c_lin9.id, "How many solutions does a linear equation in two variables have?", ["Unique solution", "Two solutions", "Infinitely many solutions", "No solution"], 2, "A linear equation in two variables has infinitely many solutions.", "understand", 0.5),
            (c_lin9.id, "If (2, 0) is a solution of 2x + 3y = k, find k:", ["2", "4", "6", "0"], 1, "2(2) + 3(0) = k => k = 4.", "apply", 0.6),
            (c_lin9.id, "The graph of the equation x = 3 is a line:", ["Parallel to x-axis", "Parallel to y-axis", "Passing through origin", "Inclined at 45 degrees"], 1, "x = constant is a vertical line parallel to the y-axis.", "understand", 0.6),

            # sci_lig8
            (c_lig8.id, "The angle of incidence is always equal to:", ["Angle of refraction", "Angle of reflection", "Angle of emergence", "90 degrees"], 1, "First law of reflection: angle of incidence = angle of reflection.", "remember", 0.3),
            (c_lig8.id, "Which type of mirror is primarily used as a rear-view mirror in vehicles?", ["Plane mirror", "Concave mirror", "Convex mirror", "Cylindrical mirror"], 2, "Convex mirrors give an erect, diminished image and a wider field of view.", "understand", 0.5),
            (c_lig8.id, "What is the focal length of a spherical mirror of radius of curvature 30 cm?", ["15 cm", "30 cm", "60 cm", "10 cm"], 0, "f = R / 2 = 30 / 2 = 15 cm.", "apply", 0.5),

            # eng_rc7
            (c_rc7.id, "Which reading strategy is best for quickly finding a specific date or name in a passage?", ["Skimming", "Scanning", "Critical reading", "Extensive reading"], 1, "Scanning is looking for specific key phrases, names, or numbers.", "understand", 0.4),
            (c_rc7.id, "What does making an 'inference' from a text mean?", ["Copying text word for word", "Drawing logical conclusions based on clues in the text", "Ignoring unfamiliar words", "Memorizing the author's biography"], 1, "An inference is a reasoned deduction based on textual evidence.", "understand", 0.5),
            (c_rc7.id, "The tone of a scientific research paper is typically:", ["Humorous and sarcastic", "Objective and factual", "Emotional and dramatic", "Poetic and whimsical"], 1, "Academic texts maintain an objective, evidence-based tone.", "analyze", 0.4),

            # sst_chr10
            (c_chr10.id, "Which of the following is an example of a primary historical source?", ["A modern history textbook", "An original diary entry written during World War I", "A 2020 documentary video", "An encyclopedia article"], 1, "Primary sources are firsthand accounts created during the time period.", "understand", 0.5),
            (c_chr10.id, "Chronology in historical inquiry refers to:", ["Studying ancient maps", "Arranging events in order of their occurrence in time", "Analyzing pottery styles", "Translating inscriptions"], 1, "Chronology is the sequential timeline of historical events.", "remember", 0.4),
            (c_chr10.id, "Why must historians cross-reference multiple historical sources?", ["To increase the word count of their papers", "To verify authenticity and eliminate author bias", "Because primary sources are always incorrect", "To avoid citing original documents"], 1, "Cross-referencing corroborates evidence and balances individual bias.", "analyze", 0.6),
        ]

        for cid, text, options, correct_idx, explanation, bloom, diff in questions_pool:
            q = Question(
                concept_id=cid,
                qtype="mcq",
                difficulty=diff,
                usage_tag="practice",
                bloom_level=bloom,
                body_en={"text": text},
                answer_data={"correct_index": correct_idx, "options": options},
                explanation_en=explanation,
                approval_status="approved",
                source="ncert",
            )
            session.add(q)

        # Add 2 questions with pending_review status for teacher review queue
        draft_q1 = Question(
            concept_id=c_mot9.id,
            qtype="mcq",
            difficulty=0.75,
            usage_tag="diagnostic",
            bloom_level="analyze",
            body_en={"text": "A vehicle decelerates uniformly from 36 km/h to rest in 5 seconds. What is the distance travelled before stopping?"},
            answer_data={"correct_index": 1, "options": ["15 m", "25 m", "30 m", "50 m"]},
            explanation_en="Initial speed u = 10 m/s, v = 0, t = 5s => a = -2 m/s². s = ut + 0.5at² = 50 - 25 = 25 m.",
            approval_status="pending_review",
            source="ai_generator",
        )
        session.add(draft_q1)

        draft_q2 = Question(
            concept_id=c_lin9.id,
            qtype="mcq",
            difficulty=0.7,
            usage_tag="practice",
            bloom_level="apply",
            body_en={"text": "The point of the form (a, -a) always lies on the line:"},
            answer_data={"correct_index": 2, "options": ["x = y", "x + y = 1", "x + y = 0", "y = -1"]},
            explanation_en="Substituting x=a and y=-a: a + (-a) = 0, which satisfies x + y = 0.",
            approval_status="pending_review",
            source="ai_generator",
        )
        session.add(draft_q2)

        await session.flush()
        print(f"Created {len(questions_pool) + 2} Questions.")

        # 9. StudentMastery records for each student across concepts (p_know between 0.2 and 0.9)
        mastery_levels = [
            # student 1 (good at math, struggling with uniform motion)
            [0.88, 0.72, 0.35, 0.22, 0.90, 0.85, 0.65, 0.75, 0.80, 0.70],
            # student 2 (moderate across board, struggling with linear equations)
            [0.85, 0.68, 0.60, 0.40, 0.75, 0.50, 0.28, 0.82, 0.85, 0.60],
            # student 3 (high achiever)
            [0.92, 0.89, 0.85, 0.80, 0.95, 0.90, 0.88, 0.91, 0.90, 0.85],
            # student 4 (struggling student)
            [0.60, 0.45, 0.30, 0.20, 0.55, 0.38, 0.25, 0.40, 0.65, 0.50],
            # student 5 (solid performer)
            [0.80, 0.75, 0.70, 0.55, 0.82, 0.78, 0.70, 0.75, 0.75, 0.68],
        ]

        all_concepts = [c_mea6, c_sdt7, c_uni8, c_mot9, c_fra6, c_alg8, c_lin9, c_lig8, c_rc7, c_chr10]

        for s_idx, sp in enumerate(student_profiles):
            scores = mastery_levels[s_idx]
            for c_idx, concept in enumerate(all_concepts):
                p = scores[c_idx]
                attempts = int(5 + p * 15)
                correct = int(attempts * p)

                sm = StudentMastery(
                    student_id=sp.id,
                    concept_id=concept.id,
                    p_know=p,
                    p_learn=0.2,
                    p_guess=0.2,
                    p_slip=0.1,
                    working_concept_id=concept.id,
                    recent_scores=[1 if i % 2 == 0 else 0 for i in range(5)],
                    total_attempts=attempts,
                    total_correct=correct,
                    last_assessed_at=now,
                    consecutive_low=3 if p < 0.40 else 0,
                    consecutive_high=3 if p >= 0.85 else 0,
                )
                session.add(sm)

        await session.flush()
        print("Created StudentMastery records for all students across curriculum concepts.")

        # 10. LevelChangeProposals (2 pending proposals for teacher review queue)
        proposal_1 = LevelChangeProposal(
            student_id=student_profiles[0].id,
            target_concept_id=c_uni8.id,
            proposed_level_concept_id=c_sdt7.id,
            proposal_type="remediation",
            evidence={
                "accuracy": 0.25,
                "consecutive_failures": 3,
                "error_patterns": ["Confusion between instantaneous speed and uniform velocity"],
            },
            narrative_en="Student Aarav Patel has 3 consecutive incorrect responses on Uniform Motion. Recommended prerequisite remediation in Speed, Distance and Time.",
            status="pending",
        )
        session.add(proposal_1)

        proposal_2 = LevelChangeProposal(
            student_id=student_profiles[1].id,
            target_concept_id=c_lin9.id,
            proposed_level_concept_id=c_alg8.id,
            proposal_type="remediation",
            evidence={
                "accuracy": 0.20,
                "consecutive_failures": 3,
                "error_patterns": ["Difficulty isolating variables with negative coefficients"],
            },
            narrative_en="Student Diya Reddy demonstrates persistent errors on Linear Equations in Two Variables. Recommended remediation back to Algebraic Expressions.",
            status="pending",
        )
        session.add(proposal_2)

        await session.commit()
        print("CHATUR database seeded successfully!")


def main():
    asyncio.run(seed_database())


if __name__ == "__main__":
    main()
