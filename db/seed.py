"""CIRCULO - Database Seeding Script
Rebuilds and populates realistic demo campus inventory, capabilities, categories,
price benchmarks, transactions, and impact events.
"""
import hashlib
from datetime import datetime, timedelta
from db.database import get_connection, init_db

def hash_pw(password: str) -> str:
    """Create a deterministic SHA-256 password hash with campus salt for demo."""
    salt = "circulo_campus_salt_2026"
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()

def seed_database():
    """Wipe and seed circulo.db with comprehensive realistic demo data."""
    print("Initializing database tables...")
    init_db(force_recreate=True)
    conn = get_connection()
    cur = conn.cursor()

    print("Seeding Users...")
    users = [
        ("Arun Kumar", "arun@campus.edu", "Computer Science & Engineering", "student", hash_pw("student123")),
        ("Sneha Rao", "sneha@campus.edu", "Electronics & Communication", "student", hash_pw("student123")),
        ("Rahul Sharma", "rahul@campus.edu", "Mechanical Engineering", "student", hash_pw("student123")),
        ("Ananya Patel", "ananya@campus.edu", "Civil Engineering", "student", hash_pw("student123")),
        ("Vikram Singh", "vikram@campus.edu", "Computer Science & Engineering", "student", hash_pw("student123")),
        ("Pooja Nair", "pooja@campus.edu", "Electronics & Communication", "student", hash_pw("student123")),
        ("CSE Hardware Lab", "cselab@campus.edu", "Computer Science & Engineering", "lab", hash_pw("lab123")),
        ("ECE IoT & Embedded Lab", "ecelab@campus.edu", "Electronics & Communication", "lab", hash_pw("lab123")),
        ("Campus Makerspace", "makerspace@campus.edu", "Central Workshop", "lab", hash_pw("lab123")),
        ("Campus Sustainability Cell", "admin@circulo.campus.edu", "Administration", "admin", hash_pw("admin123")),
    ]
    cur.executemany(
        "INSERT INTO users (name, email, department, role, password_hash) VALUES (?, ?, ?, ?, ?)",
        users
    )

    print("Seeding Categories...")
    categories = [
        (1, "Electronics", None, "gadgets circuits hardware electrical tech components"),
        (2, "Development Boards", 1, "microcontrollers boards kits mcu esp32 arduino raspberry pi embedded"),
        (3, "Sensors & Modules", 1, "detectors modules components probes ultrasonic temperature dht11"),
        (4, "Single Board Computers", 1, "sbc mini pc rpi linux computer edge computing"),
        (5, "Prototyping Accessories", 1, "wires breadboards jumper cables male to female header pins"),
        (6, "Cables & Connectivity", None, "wires cords connections interconnect display video audio"),
        (7, "Video Cables & Adapters", 6, "hdmi vga displayport projector adapter type-c converter dongle"),
        (8, "Lab & Measurement", None, "testing instruments meters workbench calibration"),
        (9, "Testing & Debugging", 8, "multimeter dmm oscilloscope probe signal generator"),
        (10, "Tools & Workshop", None, "hardware tools workshop assembly repair fabrication"),
        (11, "Prototyping Tools", 10, "soldering iron solder gun wire stripper glue gun cutter"),
        (12, "Academic & Stationery", None, "study material academics books exam supplies drawing"),
        (13, "Calculators", 12, "scientific calculator casio fx-991 classwiz matrix solver"),
        (14, "Textbooks", 12, "reference books study materials engineering syllabus syllabus books"),
        (15, "Drawing Tools", 12, "drafter mini drafter ed kit engineering graphics drawing sheet board"),
    ]
    cur.executemany(
        "INSERT INTO categories (id, name, parent_id, synonyms) VALUES (?, ?, ?, ?)",
        categories
    )

    print("Seeding Price References for Decision Engine...")
    prices = [
        ("esp32", 120.0, 320.0, 580.0, "ESP32 DevKit WROOM-32"),
        ("arduino uno", 90.0, 280.0, 550.0, "Arduino Uno R3 DIP/SMD"),
        ("arduino nano", 70.0, 180.0, 320.0, "Arduino Nano V3 ATmega328P"),
        ("raspberry pi", 450.0, 3200.0, 5400.0, "Raspberry Pi 4 Model B (4GB)"),
        ("hdmi cable", 60.0, 150.0, 399.0, "High-Speed HDMI 1.5m"),
        ("usb-c to hdmi adapter", 100.0, 350.0, 799.0, "USB-C to HDMI 4K Converter"),
        ("vga adapter", 80.0, 180.0, 349.0, "HDMI to VGA with Audio Jack"),
        ("digital multimeter", 150.0, 450.0, 950.0, "Auto-Ranging Digital Multimeter"),
        ("soldering iron", 80.0, 220.0, 480.0, "60W Temperature Controlled Iron"),
        ("scientific calculator", 120.0, 650.0, 1495.0, "Casio fx-991EX ClassWiz"),
        ("ultrasonic sensor", 40.0, 90.0, 160.0, "HC-SR04 Ultrasonic Sensor"),
        ("dht11 sensor", 35.0, 80.0, 140.0, "DHT11 Temp & Humidity Module"),
        ("breadboard and jumper wires", 30.0, 110.0, 240.0, "830-Point Breadboard + 65 Wires"),
        ("engineering drawing kit", 120.0, 450.0, 980.0, "Omega Mini Drafter & Board Kit"),
        ("higher engineering mathematics", 50.0, 380.0, 890.0, "B.S. Grewal 44th Edition"),
    ]
    cur.executemany(
        "INSERT INTO price_reference (item_key, repair_cost, used_price, new_price, note) VALUES (?, ?, ?, ?, ?)",
        prices
    )

    now = datetime.now()
    def date_days_ago(days):
        return (now - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    print("Seeding Items...")
    items = [
        # (id, owner_id, name, category_id, desc, condition, location, qty, qty_avail, avail, avail_for, avail_until, last_used)
        (1, 7, "ESP32 Wi-Fi & Bluetooth Dev Board (NodeMCU-32S)", 2, 
         "Dual-core Xtensa 32-bit LX6 with built-in Wi-Fi and Bluetooth. Pre-flashed with MicroPython, breadboard ready.",
         "Good", "CSE Hardware Lab, Room 302", 4, 4, "AVAILABLE", "borrow", None, date_days_ago(5)),
        
        (2, 2, "Arduino Uno R3 Original Board", 2, 
         "Standard Arduino Uno with ATmega328P microcontroller. Ideal for basic robotics and beginner microcomputing projects.",
         "Good", "ECE Hostel Block B, Room 214", 2, 2, "AVAILABLE", "borrow", None, date_days_ago(8)),

        (3, 5, "Arduino Nano V3 (CH340 chip)", 2, 
         "Compact breadboard-friendly microcontroller with USB Mini-B connection. Works with Arduino IDE.",
         "New", "CSE Hostel Block A, Room 108", 1, 1, "AVAILABLE", "both", None, date_days_ago(12)),

        (4, 9, "Raspberry Pi 4 Model B (4GB RAM)", 4, 
         "Quad core 64-bit ARM CPU, 4GB RAM, dual 4K micro-HDMI outputs, Gigabit Ethernet and Wi-Fi. Includes 32GB SD card with Raspberry Pi OS.",
         "Good", "Campus Makerspace, Lab Bench 4", 2, 2, "AVAILABLE", "borrow", None, date_days_ago(3)),

        (5, 7, "High-Speed HDMI 2.0 Cable (1.8m, Gold-Plated)", 7, 
         "Supports 4K @ 60Hz. Heavy-duty braided cable for connecting laptop to auditorium or seminar hall projector.",
         "Good", "CSE Hardware Lab, Front Desk", 3, 3, "AVAILABLE", "borrow", None, date_days_ago(1)),

        (6, 1, "USB-C to HDMI 4K Display Adapter (Thunderbolt 3/4 compatible)", 7, 
         "Compact aluminum adapter. Connects MacBook, iPad or modern Dell/HP USB-C laptops directly to classroom projectors and monitors.",
         "New", "CSE Hostel Block A, Room 312", 1, 1, "AVAILABLE", "borrow", None, date_days_ago(4)),

        (7, 8, "Active HDMI to VGA Converter with 3.5mm Audio", 7, 
         "Converts modern HDMI laptop output to legacy VGA projectors in older lecture halls. Includes 3.5mm stereo audio output.",
         "Good", "ECE IoT Lab, Equipment Rack 2", 2, 2, "AVAILABLE", "borrow", None, date_days_ago(14)),

        (8, 2, "Casio fx-991EX ClassWiz Scientific Calculator", 13, 
         "552 functions, high-resolution natural textbook display, matrix/vector/equation solver. Permitted for semester exams.",
         "Good", "ECE Hostel Block B, Room 214", 1, 1, "AVAILABLE", "borrow", None, date_days_ago(2)),

        (9, 8, "Auto-Ranging Digital Multimeter with Temperature Probe", 9, 
         "Measures AC/DC Voltage, Current, Resistance, Capacitance, Frequency and Continuity with audible buzzer.",
         "Good", "ECE IoT Lab, Workbench 3", 3, 3, "AVAILABLE", "borrow", None, date_days_ago(6)),

        (10, 9, "60W Adjustable Temperature Soldering Iron Kit", 11, 
         "Temperature range 200°C-450°C. Comes with stand, solder wire, desoldering pump, and tweezer set.",
         "Good", "Campus Makerspace, Soldering Station", 2, 2, "AVAILABLE", "borrow", None, date_days_ago(2)),

        (11, 5, "HC-SR04 Ultrasonic Distance Sensor Modules (Pack of 2)", 3, 
         "2cm to 400cm non-contact distance measurement module. Ideal for obstacle avoiding robots.",
         "New", "CSE Hostel Block A, Room 108", 4, 4, "AVAILABLE", "both", None, date_days_ago(10)),

        (12, 2, "DHT11 Digital Temperature and Humidity Sensor", 3, 
         "Single-wire digital sensor module for weather stations and IoT environmental logging.",
         "Good", "ECE Hostel Block B, Room 214", 3, 3, "AVAILABLE", "borrow", None, date_days_ago(15)),

        (13, 1, "830-Point Solderless Breadboard with 65 Male-to-Male Jumper Wires", 5, 
         "Full size breadboard with power rails plus flexible multicolour jumper cables for fast circuit breadboarding.",
         "Good", "CSE Hostel Block A, Room 312", 3, 3, "AVAILABLE", "both", None, date_days_ago(7)),

        (14, 4, "Mini Drafter & Engineering Drawing Board Kit", 15, 
         "Omega mini drafter with clamp, stainless steel scale, drafting clips, and A2 wooden drawing board. Essential for 1st year Engineering Graphics.",
         "Good", "Civil Dept Student Lounge", 1, 1, "AVAILABLE", "borrow", None, date_days_ago(9)),

        (15, 3, "Higher Engineering Mathematics by B.S. Grewal (44th Edition)", 14, 
         "Comprehensive textbook covering calculus, matrices, Fourier series, transforms and numerical methods.",
         "Good", "Mechanical Hostel Block C, Room 405", 2, 2, "AVAILABLE", "borrow", None, date_days_ago(18)),

        # Resource Rescue items (Idle items: last_used > 30 days)
        (16, 7, "8051 Microcontroller Trainer Kit (Anshuman Tech)", 2, 
         "Complete 8051 development trainer board with 7-segment display, matrix keypad and serial interface. Stored in storage rack.",
         "Fair", "CSE Hardware Lab, Rack C", 3, 3, "AVAILABLE", "both", None, date_days_ago(85)),

        (17, 8, "Texas Instruments MSP430 LaunchPad Development Kit", 2, 
         "Ultra-low power MSP430G2553 microcontroller board with onboard emulator. Sitting idle since last semester lab exam.",
         "Good", "ECE IoT Lab, Cabinet 1", 2, 2, "AVAILABLE", "both", None, date_days_ago(72)),

        (18, 9, "VGA to VGA Video Cable (5 meters, Heavy Shielded)", 7, 
         "Long VGA cable for legacy projector setups. Unused since seminar hall HDMI upgrade.",
         "Good", "Campus Makerspace, Cable Bin", 4, 4, "AVAILABLE", "donate", None, date_days_ago(65)),

        (19, 3, "Mechanical Engineering Thermodynamics by P.K. Nag", 14, 
         "Core textbook for 2nd year thermal engineering. Idle since last semester completed.",
         "Good", "Mechanical Hostel Block C, Room 405", 1, 1, "AVAILABLE", "both", None, date_days_ago(54)),

        (20, 9, "Analog Oscilloscope 20MHz Dual Trace (Scientech 801C)", 9, 
         "Dual channel analog cathode-ray oscilloscope. Operational but superseded by digital oscilloscopes.",
         "Fair", "Campus Makerspace, Back Storage", 1, 1, "AVAILABLE", "borrow", None, date_days_ago(92)),

        (21, 6, "ST-Link V2 STM8/STM32 Programmer & Debugger", 2, 
         "USB in-circuit debugger and programmer for STM32 Cortex microcontrollers. Unused after capstone project.",
         "New", "ECE Hostel Block B, Room 305", 1, 1, "AVAILABLE", "borrow", None, date_days_ago(41)),

        # Damaged items for Repair route demo
        (22, 9, "Soldering Iron Station (Loose Ceramic Heating Element)", 11, 
         "50W soldering iron station; heating element is intermittently loose and needs re-crimping or replacement element (cost ~₹80).",
         "Fair", "Campus Makerspace, Repair Shelf", 1, 1, "AVAILABLE", "both", None, date_days_ago(35)),

        (23, 7, "Arduino Uno Board with Broken USB Type-B Jack", 2, 
         "Board electronics are intact but USB-B connector loosened from solder pads. Repairable in 15 mins at makerspace.",
         "Fair", "CSE Hardware Lab, Scrap Box", 1, 1, "AVAILABLE", "both", None, date_days_ago(45)),
    ]

    cur.executemany(
        """INSERT INTO items (
            id, owner_id, name, category_id, description, condition, location,
            quantity, quantity_available, availability, available_for, available_until, last_used
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        items
    )

    print("Seeding Item Capabilities...")
    capabilities_data = [
        # ESP32
        (1, "microcontroller"), (1, "wifi"), (1, "bluetooth"), (1, "iot"), (1, "gpio"), (1, "prototyping"), (1, "embedded"),
        # Arduino Uno
        (2, "microcontroller"), (2, "gpio"), (2, "analog input"), (2, "prototyping"), (2, "embedded"), (2, "5v logic"), (2, "iot"),
        # Arduino Nano
        (3, "microcontroller"), (3, "gpio"), (3, "analog input"), (3, "prototyping"), (3, "compact"), (3, "breadboard friendly"), (3, "iot"),
        # Raspberry Pi
        (4, "single board computer"), (4, "linux"), (4, "wifi"), (4, "bluetooth"), (4, "hdmi output"), (4, "usb 3.0"), (4, "iot"), (4, "python"),
        # HDMI Cable
        (5, "video transmission"), (5, "hdmi"), (5, "display output"), (5, "projector connection"), (5, "monitor connection"), (5, "audio transmission"),
        # USB-C to HDMI
        (6, "video transmission"), (6, "hdmi"), (6, "usb-c"), (6, "projector connection"), (6, "macbook display"), (6, "type-c video"),
        # VGA Adapter
        (7, "video transmission"), (7, "vga"), (7, "legacy projector"), (7, "projector connection"), (7, "analog display"),
        # Scientific Calculator
        (8, "scientific calculation"), (8, "matrix calculation"), (8, "equation solver"), (8, "statistics"), (8, "exam approved"),
        # Multimeter
        (9, "voltage measurement"), (9, "current measurement"), (9, "resistance measurement"), (9, "continuity test"), (9, "circuit debugging"),
        # Soldering Iron
        (10, "soldering"), (10, "pcb assembly"), (10, "wire joining"), (10, "electronics repair"), (10, "hardware prototyping"),
        # Ultrasonic Sensor
        (11, "distance measurement"), (11, "obstacle detection"), (11, "robotics"), (11, "gpio"), (11, "5v logic"),
        # DHT11 Sensor
        (12, "temperature measurement"), (12, "humidity measurement"), (12, "weather monitoring"), (12, "gpio"), (12, "iot"),
        # Breadboard
        (13, "prototyping"), (13, "circuit building"), (13, "solderless testing"), (13, "gpio connections"),
        # Drawing Kit
        (14, "drafting"), (14, "engineering drawing"), (14, "geometric construction"), (14, "t-square"), (14, "compass set"),
        # Math Textbook
        (15, "calculus"), (15, "differential equations"), (15, "linear algebra"), (15, "engineering math"), (15, "reference book"),
        # 8051 Trainer
        (16, "microcontroller"), (16, "8051"), (16, "assembly programming"), (16, "embedded"), (16, "legacy training"),
        # MSP430
        (17, "microcontroller"), (17, "low power"), (17, "ti launchpad"), (17, "embedded"), (17, "adc"),
        # VGA Cable
        (18, "video transmission"), (18, "vga"), (18, "projector connection"), (18, "monitor connection"),
        # Thermo Textbook
        (19, "thermodynamics"), (19, "mechanical engineering"), (19, "heat transfer"), (19, "reference book"),
        # Analog Scope
        (20, "signal observation"), (20, "waveform analysis"), (20, "oscilloscope"), (20, "circuit debugging"),
        # ST-Link
        (21, "microcontroller programmer"), (21, "stm32 debugger"), (21, "swd"), (21, "firmware flashing"),
        # Damaged Iron
        (22, "soldering"), (22, "electronics repair"), (22, "requires repair"),
        # Damaged Arduino
        (23, "microcontroller"), (23, "prototyping"), (23, "requires repair"),
    ]
    cur.executemany("INSERT INTO item_capabilities (item_id, capability) VALUES (?, ?)", capabilities_data)

    print("Seeding Sample Completed Transactions & Impact Events...")
    # Past completed borrow transactions
    past_transactions = [
        (1, 5, 7, 1, None, date_days_ago(25), date_days_ago(18), date_days_ago(19), "RETURNED"),
        (2, 8, 2, 5, None, date_days_ago(20), date_days_ago(13), date_days_ago(14), "RETURNED"),
        (3, 4, 9, 1, None, date_days_ago(15), date_days_ago(8), date_days_ago(9), "RETURNED"),
        (4, 9, 8, 3, None, date_days_ago(12), date_days_ago(5), date_days_ago(6), "RETURNED"),
        (5, 14, 4, 2, None, date_days_ago(30), date_days_ago(16), date_days_ago(17), "RETURNED"),
    ]
    cur.executemany(
        """INSERT INTO transactions (
            id, item_id, lender_id, borrower_id, request_id, start_date, due_date, returned_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        past_transactions
    )

    impacts = [
        # tx 1: HDMI cable borrowed instead of bought new
        (1, 1, 5, 1, "borrow", "item_reused", 1.0, "Physical loan successfully returned to CSE Lab"),
        (2, 1, 5, 1, "borrow", "purchase_avoided", 1.0, "Verified substitute for single-use event purchase"),
        (3, 1, 5, 1, "borrow", "money_saved", 399.0, "Avoided retail purchase of 1.5m HDMI Cable (₹399)"),

        # tx 2: Calculator borrowed during mid-term exam
        (4, 5, 8, 2, "borrow", "item_reused", 1.0, "Peer-to-peer loan returned in good condition"),
        (5, 5, 8, 2, "borrow", "purchase_avoided", 1.0, "Exam calculator borrowed rather than purchased new"),
        (6, 5, 8, 2, "borrow", "money_saved", 1495.0, "Avoided retail purchase of Casio fx-991EX (₹1,495)"),

        # tx 3: Raspberry Pi 4 borrowed for 1-week demo
        (7, 1, 4, 3, "borrow", "item_reused", 1.0, "Makerspace asset recirculated for capstone test"),
        (8, 1, 4, 3, "borrow", "purchase_avoided", 1.0, "Prototyped using existing shared Pi rather than buying new unit"),
        (9, 1, 4, 3, "borrow", "money_saved", 5400.0, "Avoided retail purchase of Raspberry Pi 4 4GB (₹5,400)"),

        # tx 4: Multimeter borrowed for debugging
        (10, 3, 9, 4, "borrow", "item_reused", 1.0, "ECE IoT Lab equipment loaned for mini-project"),
        (11, 3, 9, 4, "borrow", "money_saved", 950.0, "Avoided retail purchase of Digital Multimeter (₹950)"),

        # tx 5: Mini Drafter borrowed for 1st year graphics
        (12, 2, 14, 5, "borrow", "item_reused", 1.0, "Reused senior drawing kit for graphics practicals"),
        (13, 2, 14, 5, "borrow", "purchase_avoided", 1.0, "Avoided buying new single-semester drafting kit"),
        (14, 2, 14, 5, "borrow", "money_saved", 980.0, "Avoided retail purchase of Engineering Drawing Kit (₹980)"),
    ]
    cur.executemany(
        """INSERT INTO impact_events (
            id, user_id, item_id, transaction_id, action, metric_type, estimated_value, methodology
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        impacts
    )

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
