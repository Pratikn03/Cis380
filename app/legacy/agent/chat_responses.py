"""Enhanced chat responses for SentinelForge offline mode with varied responses."""

from __future__ import annotations

import random


# ============================================================================
# VARIED GREETING RESPONSES
# ============================================================================
GREETINGS = [
    """Hello! I'm SentinelForge, your intelligent assistant!

I can help you with:
• **Fraud Detection** - Analyze transaction risk patterns
• **Cyber Security** - Detect network threats & anomalies  
• **Movie Recommendations** - Get personalized suggestions
• **Machine Learning** - Understand ML concepts
• **Document Search** - Search uploaded docs (RAG)

Just type your question or try: "recommend a movie" or "what is fraud detection?" """,

    """Hi there! Welcome to SentinelForge! 🛡️

I'm your AI-powered security and recommendation assistant. Here's what I can do:
• Detect fraud patterns in transactions
• Analyze cybersecurity threats
• Recommend movies, products & more
• Answer questions about ML & AI
• Search through your documents

What would you like to explore today?""",

    """Welcome! I'm SentinelForge - built by Pratik Niroula! 👋

**Quick Actions:**
→ Say "recommend action movies" for suggestions
→ Ask "what is anomaly detection?" to learn
→ Say "help" to see all my capabilities

I specialize in security analytics, machine learning, and intelligent recommendations. How can I assist you?""",

    """Hey! Great to see you! I'm your intelligent assistant.

**Popular commands:**
• "Recommend a comedy movie"
• "Explain fraud detection"
• "What is machine learning?"
• "Tell me about cybersecurity"

I work offline with smart responses - no API needed! What's on your mind?"""
]


# ============================================================================
# VARIED HELP RESPONSES
# ============================================================================
HELP_RESPONSES = [
    """**SentinelForge Capabilities** 🚀

**💬 Chat Features:**
• Ask any question - I'll provide intelligent responses
• Request recommendations for movies, products, courses
• Learn about fraud detection, cybersecurity, ML

**🎬 Recommendations:**
• "Recommend a movie" - Get varied movie picks
• "Recommend action movies" - Genre-specific
• "Movies like Inception" - Similar titles

**🔍 Security Analysis:**
• Fraud detection patterns
• Cyber threat analysis
• Behavioral anomaly detection

**📚 Knowledge Areas:**
• Machine Learning & AI
• Anomaly Detection
• Data Science concepts

Try asking: "What is fraud detection?" or "Recommend sci-fi movies" """,

    """**What can I help you with?** 🤖

**1. Movie Recommendations**
   • "Recommend a movie" → Random great picks
   • "Action movies" → Genre filtering
   • "Movies like The Matrix" → Similar films

**2. Security & Fraud**
   • Fraud detection methods
   • Cybersecurity concepts
   • Anomaly detection techniques

**3. Machine Learning**
   • ML algorithms explained
   • Deep learning concepts
   • Model training basics

**4. General Knowledge**
   • AI/ML topics
   • Tech explanations
   • Best practices

Just type your question naturally - I'll understand!""",

    """**SentinelForge Help Guide** 📖

I'm an offline-capable AI assistant. Here's how to use me:

**🎯 Recommendations:**
• Say "recommend" + category (movies, action, comedy, etc.)
• Ask for "movies like [title]" for similar suggestions

**❓ Questions:**
• "What is [topic]?" - I'll explain it
• "How does [concept] work?" - Technical details
• "Tell me about [subject]" - Overview

**🛡️ Security Topics:**
• Fraud detection
• Cyber threats  
• Anomaly detection
• Behavioral analysis

**💡 Pro Tips:**
• I give different answers each time - try asking again!
• Be specific for better results
• I work 100% offline - no internet needed!"""
]


# ============================================================================
# VARIED ABOUT RESPONSES  
# ============================================================================
ABOUT_RESPONSES = [
    """**About SentinelForge** 🛡️

I'm SentinelForge - a comprehensive AI assistant built by **Pratik Niroula**!

**My Capabilities:**
• Natural language understanding
• Intelligent recommendations (movies, products, courses)
• Fraud & cybersecurity analysis
• Document search & retrieval (RAG)
• Offline operation - no API required!

**Tech Stack:**
• FastAPI backend
• React/TypeScript frontend
• PyTorch & scikit-learn models
• 150K+ training samples

Built as part of a machine learning portfolio project showcasing anomaly detection and intelligent systems.""",

    """**Who am I?** 🤖

I'm **SentinelForge** - an AI assistant created by Pratik Niroula for the CIS380 project.

**What makes me special:**
✓ Work completely offline
✓ Give varied, intelligent responses  
✓ Recommend movies from 60K+ titles
✓ Explain ML & security concepts
✓ Learn from documents (RAG)

**My brain includes:**
• Fraud detection models (99.2% accuracy)
• Cybersecurity threat analysis
• Behavioral anomaly detection
• Natural language understanding

I'm proof that AI can be smart without always needing the cloud!""",

    """**SentinelForge Info** ℹ️

Created by: **Pratik Niroula**
Purpose: ML Portfolio & Anomaly Detection Demo

**Core Features:**
• 🎬 Movie recommendations (60K+ films)
• 🛡️ Fraud detection analysis
• 🔐 Cybersecurity insights
• 🧠 ML concept explanations
• 📄 Document Q&A (RAG)

**Technical Details:**
• Backend: FastAPI + Python 3.13
• Frontend: React + TypeScript
• Models: PyTorch, scikit-learn
• Database: 154K+ images, 60K movies

This project demonstrates real-world ML applications in security and recommendations."""
]


# ============================================================================
# VARIED TRAINING/DEMO RESPONSES
# ============================================================================
TRAINING_RESPONSES = [
    """**Getting Started with SentinelForge** 🚀

**Quick Start:**
1. The server is running at `http://localhost:8000`
2. Try the chat: Ask "recommend a movie"
3. Explore: "what is fraud detection?"

**Ready Features:**
✓ Movie recommendations (varied each time!)
✓ Fraud/cyber/ML explanations
✓ Document search (add files to `data/docs/`)

**Try These Commands:**
• "Recommend comedy movies"
• "Explain machine learning"
• "What is anomaly detection?"

No setup needed - just start chatting!""",

    """**What's Next?** 🎯

**You can do right now:**
• Chat with me - I give varied intelligent responses
• Get movie recommendations - different every time
• Learn about fraud detection, cybersecurity, ML

**Advanced Features:**
• Add OpenAI API key for enhanced responses
• Upload documents for RAG search
• Connect from GitHub Pages via ngrok

**Explore the Project:**
• `/api/docs` - API documentation
• `/api/chat` - Chat endpoint
• Check out the React frontend!

What would you like to try?"""
]


# ============================================================================
# VARIED FALLBACK RESPONSES
# ============================================================================
FALLBACK_RESPONSES = [
    """Hmm, I don't have specific information on that topic, but I can help with:

• **Movie recommendations** - "Recommend a movie"
• **Fraud detection** - "What is fraud detection?"
• **Cybersecurity** - "Explain cyber threats"
• **Machine learning** - "How does ML work?"

Try rephrasing your question or ask about one of these topics!""",

    """That's an interesting question! While I don't have details on that specific topic, here's what I'm great at:

🎬 **Recommendations**: "Recommend action movies"
🛡️ **Security**: "What is anomaly detection?"
🧠 **ML/AI**: "Explain deep learning"

Feel free to ask about any of these!""",

    """I searched my knowledge base but couldn't find that specific information.

**Here's what I know well:**
• Fraud detection patterns and methods
• Cybersecurity threats and defenses
• Machine learning concepts
• Movie recommendations (60K+ titles!)

**Try asking:**
• "Recommend a thriller movie"
• "What is behavioral analysis?"
• "How does fraud detection work?"

I'll give you a great answer on these topics!""",

    """I'm not sure about that one, but I'd love to help with something else!

**My specialties:**
→ Movie recommendations (ask again for different picks!)
→ Fraud & security concepts
→ Machine learning explanations
→ Anomaly detection methods

What else would you like to know?"""
]


# ============================================================================
# TOPIC-SPECIFIC KNOWLEDGE BASE
# ============================================================================
KNOWLEDGE_BASE = {
    "fraud": [
        """**Fraud Detection Explained** 🛡️

Fraud detection uses machine learning to identify suspicious patterns in transactions. 

**Key Techniques:**
• **Anomaly Detection** - Find unusual patterns
• **Behavioral Analysis** - Track user behavior changes
• **Rule-Based Systems** - Known fraud patterns
• **Ensemble Methods** - Combine multiple models

**Common Fraud Indicators:**
• Unusual transaction amounts
• Geographic anomalies
• Velocity (rapid transactions)
• Device fingerprint changes

Our models achieve 99.2% detection accuracy!""",

        """**How Fraud Detection Works** 💡

Modern fraud detection systems analyze multiple signals in real-time:

**Transaction Features:**
• Amount, time, location
• Merchant category
• Payment method

**Behavioral Signals:**
• Purchase patterns
• Login locations
• Device characteristics

**ML Models Used:**
• Random Forests
• Gradient Boosting (XGBoost)
• Neural Networks
• Isolation Forests

The key is combining multiple weak signals into strong predictions.""",

        """**Fraud Detection in Practice** 🔍

Real-world fraud detection involves:

**1. Feature Engineering**
   - Transaction velocity
   - Amount deviation from average
   - Geographic risk scores

**2. Model Training**
   - Historical fraud cases
   - Imbalanced learning techniques
   - Cross-validation

**3. Real-time Scoring**
   - Sub-second predictions
   - Risk thresholds
   - Human review queues

**4. Continuous Learning**
   - Fraud patterns evolve
   - Models need retraining
   - Feedback loops

This project includes a fraud model trained on 100K+ transactions!"""
    ],
    
    "cyber": [
        """**Cybersecurity Fundamentals** 🔐

Cybersecurity protects systems, networks, and data from digital attacks.

**Key Areas:**
• **Network Security** - Firewalls, IDS/IPS
• **Application Security** - Secure coding, testing
• **Endpoint Security** - Antivirus, EDR
• **Identity Management** - Authentication, access control

**Common Threats:**
• Phishing attacks
• Malware & ransomware
• DDoS attacks
• Insider threats

Defense requires multiple layers of protection!""",

        """**Understanding Cyber Threats** ⚠️

Modern cyber threats include:

**External Threats:**
• Phishing - Deceptive emails/sites
• Malware - Viruses, trojans, worms
• Ransomware - Encrypts data for payment
• DDoS - Overwhelms services

**Internal Threats:**
• Insider attacks
• Accidental data exposure
• Credential compromise

**Protection Strategies:**
• Zero-trust architecture
• Multi-factor authentication
• Regular security training
• Incident response planning

Stay vigilant and keep systems updated!""",

        """**Cybersecurity Best Practices** ✅

Protect yourself and your organization:

**For Individuals:**
• Use strong, unique passwords
• Enable 2FA everywhere
• Be cautious with links/attachments
• Keep software updated

**For Organizations:**
• Implement zero-trust
• Regular security audits
• Employee training
• Incident response plans
• Data encryption

**Detection Methods:**
• SIEM systems
• Behavioral analytics
• Network monitoring
• Threat intelligence

Security is a continuous process, not a destination!"""
    ],
    
    "machine learning": [
        """**Machine Learning Explained** 🧠

Machine learning enables computers to learn from data without explicit programming.

**Types of ML:**
• **Supervised Learning** - Learn from labeled examples
• **Unsupervised Learning** - Find patterns in unlabeled data
• **Reinforcement Learning** - Learn through trial and error

**Common Algorithms:**
• Linear/Logistic Regression
• Decision Trees & Random Forests
• Neural Networks
• Clustering (K-means, DBSCAN)

**Applications:**
• Image recognition
• Fraud detection
• Recommendations
• Natural language processing

ML is transforming every industry!""",

        """**How Machine Learning Works** ⚙️

The ML process involves:

**1. Data Collection**
   - Gather relevant data
   - Ensure quality and quantity

**2. Feature Engineering**
   - Select important attributes
   - Transform raw data

**3. Model Training**
   - Choose algorithm
   - Fit to training data
   - Tune hyperparameters

**4. Evaluation**
   - Test on held-out data
   - Measure accuracy, precision, recall

**5. Deployment**
   - Serve predictions
   - Monitor performance
   - Retrain as needed

This project uses ML for fraud detection, recommendations, and more!""",

        """**Deep Learning & Neural Networks** 🔮

Deep learning uses multi-layer neural networks:

**Architecture:**
• Input layer - Receives data
• Hidden layers - Learn features
• Output layer - Makes predictions

**Popular Architectures:**
• CNNs - Image processing
• RNNs/LSTMs - Sequential data
• Transformers - Language models
• GANs - Generative models

**Why "Deep"?**
• Multiple hidden layers
• Learns hierarchical features
• Automatic feature extraction

Deep learning excels at:
• Computer vision
• Natural language processing
• Speech recognition
• Game playing (AlphaGo!)"""
    ],
    
    "anomaly": [
        """**Anomaly Detection Explained** 📊

Anomaly detection identifies unusual patterns that don't conform to expected behavior.

**Methods:**
• **Statistical** - Z-scores, IQR
• **Distance-based** - KNN, LOF
• **Density-based** - DBSCAN
• **Model-based** - Isolation Forest, Autoencoders

**Applications:**
• Fraud detection
• Network intrusion detection
• System health monitoring
• Quality control

**Challenges:**
• Defining "normal"
• Handling concept drift
• Balancing false positives/negatives

This project specializes in anomaly detection!""",

        """**Types of Anomalies** 🎯

Anomalies come in different forms:

**Point Anomalies:**
• Single unusual data points
• Example: One huge transaction

**Contextual Anomalies:**
• Unusual in specific context
• Example: AC usage in winter

**Collective Anomalies:**
• Groups of related anomalies
• Example: Coordinated attack pattern

**Detection Approaches:**
• Supervised - Known anomaly labels
• Unsupervised - Find outliers
• Semi-supervised - Few labeled examples

Understanding anomaly types helps choose the right detection method!""",

        """**Anomaly Detection in Practice** 🔧

Real-world anomaly detection involves:

**1. Establish Baseline**
   - Learn normal behavior
   - Define features
   - Set thresholds

**2. Monitor Continuously**
   - Real-time scoring
   - Alert generation
   - Dashboard visualization

**3. Investigate Alerts**
   - Triage by severity
   - Root cause analysis
   - Document findings

**4. Adapt & Improve**
   - Update models
   - Reduce false positives
   - Handle new patterns

This project includes anomaly detection for fraud, cyber, and behavior!"""
    ],

    "recommend": [
        """**How Recommendations Work** 🎬

Our recommendation system uses multiple techniques:

**Content-Based Filtering:**
• Analyzes item attributes (genres, actors)
• Matches to user preferences

**Collaborative Filtering:**
• "Users like you also liked..."
• Finds similar user patterns

**Hybrid Approaches:**
• Combines multiple methods
• Better accuracy

**Our Movie Database:**
• 60,000+ titles
• Genre, year, ratings
• Popularity scores

Try "recommend action movies" or "movies like Inception"!""",

        """**Recommendation Systems Explained** 💡

How we suggest content:

**Data Sources:**
• MovieLens dataset (60K movies)
• Genre classifications
• Popularity metrics
• User ratings

**Algorithms:**
• TF-IDF for text similarity
• Cosine similarity matching
• Random sampling for variety

**Features:**
• Genre filtering
• Similar movie lookup
• Randomized results (different each time!)

Ask for recommendations and get fresh suggestions every time!"""
    ]
}


def get_greeting_response() -> str:
    """Return a varied friendly greeting."""
    return random.choice(GREETINGS)


def get_help_response() -> str:
    """Return varied help information."""
    return random.choice(HELP_RESPONSES)


def get_training_response() -> str:
    """Return varied training/demo guidance."""
    return random.choice(TRAINING_RESPONSES)


def get_about_response() -> str:
    """Return varied about/info response."""
    return random.choice(ABOUT_RESPONSES)


def get_fallback_response() -> str:
    """Return varied fallback when no specific answer found."""
    return random.choice(FALLBACK_RESPONSES)


def get_topic_response(topic: str) -> str | None:
    """Get a response for a specific topic from the knowledge base."""
    topic_lower = topic.lower()
    for key, responses in KNOWLEDGE_BASE.items():
        if key in topic_lower:
            return random.choice(responses)
    return None


def is_greeting(text: str) -> bool:
    """Check if text is a greeting."""
    lower = text.lower()
    return any(
        k in lower
        for k in ("hello", "hi ", "hey", "greet", "good morning", "good afternoon", "good evening", "howdy", "what's up", "sup")
    )


def is_help_request(text: str) -> bool:
    """Check if text is asking for help."""
    lower = text.lower()
    return any(
        k in lower for k in ("help", "what can you do", "capabilities", "features", "how to use", "how do i", "what do you do")
    )


def is_training_request(text: str) -> bool:
    """Check if text is asking about training/demo."""
    lower = text.lower()
    return any(
        k in lower
        for k in (
            "next step",
            "next steps",
            "what are we doing",
            "what to do",
            "train",
            "training",
            "demo",
            "get started",
            "start",
        )
    )


def is_about_request(text: str) -> bool:
    """Check if text is asking about the bot."""
    lower = text.lower()
    return any(k in lower for k in ("about", "who are you", "what are you", "your name", "who made", "who built", "who created"))


def get_enhanced_response(message: str) -> str | None:
    """Get enhanced response based on message type.

    Returns varied responses - different each time!
    """
    if not message or not message.strip():
        return get_greeting_response()

    if is_greeting(message):
        return get_greeting_response()

    if is_help_request(message):
        return get_help_response()

    if is_training_request(message):
        return get_training_response()

    if is_about_request(message):
        return get_about_response()
    
    # Check knowledge base for topic-specific responses
    topic_response = get_topic_response(message)
    if topic_response:
        return topic_response

    return None
