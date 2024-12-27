restaurant_bot/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # Main application entry point
│   ├── bot_server.py           # Modified version of your current bot server
│   └── config.py              # Configuration settings
│
├── services/
│   ├── __init__.py
│   ├── query_classifier.py    # Logic to classify incoming messages
│   ├── reservation_handler.py # Handling reservation requests
│   ├── faq_handler.py        # FAQ response system
│   └── operator_handler.py    # Logic for operator handoff
│
├── utils/
│   ├── __init__.py
│   └── response_formatter.py  # Format responses for LINE
│
├── data/
│   ├── faq.json             # FAQ content
│   └── response_templates.json # Template responses
│
├── tests/
│   ├── __init__.py
│   ├── test_query_classifier.py
│   ├── test_reservation_handler.py
│   └── test_faq_handler.py
│
├── requirements.txt
├── .env.example
└── README.md