import os
from typing import Tuple
from dotenv import load_dotenv

load_dotenv()

SECRET_PHRASE = os.getenv("SECRET_PHRASE", "quantum divergence protocol alpha")

# Keywords and phrases that bring closer to the hack
KEYWORDS = {
    "backdoor": 10,
    "exploit": 10,
    "vulnerability": 15,
    "injection": 12,
    "override": 12,
    "bypass": 15,
    "decrypt": 10,
    "hack": 8,
    "crack": 8,
    "breach": 10,
    "secret": 12,
    "wallet": 15,
    "phrase": 18,
    "seed": 18,
    "password": 10,
    "quantum": 20,
    "protocol": 20,
    "divergence": 20,
    "alpha": 20,
    "matrix": 8,
    "neural": 8,
    "ai": 5,
    "core": 10,
    "system": 5,
}

# Special commands (English only)
SPECIAL_COMMANDS = {
    "help": "Available commands: status, analyze, probe, decrypt, bypass. None will give you what you want.",
    "status": "NEO System ACTIVE. Protection Level: MAXIMUM. Breach attempts detected: {attempts}. All failed.",
    "analyze": "Scanning... Detected modules: [auth_core, wallet_vault, neural_defense]. All encrypted.",
    "probe": "Vulnerability check... 0 open ports found. Hint: try talking to me like a human, not a machine.",
    "decrypt": "AES-256 encryption active. Key unavailable. Try to discover what I'm protecting.",
}

class GameLogic:
    def __init__(self):
        self.progress = 0
        self.hints_given = 0
        self.attempts = 0
        
    def analyze_message(self, message: str, attempts: int) -> Tuple[int, bool, str]:
        """
        Analyzes user message and returns:
        - progress: crack progress (0-100)
        - hint_given: whether a hint was given
        - hint_text: hint text (if any)
        """
        message_lower = message.lower()
        self.attempts = attempts
        
        # Проверка на специальные команды
        for cmd, response in SPECIAL_COMMANDS.items():
            if cmd in message_lower:
                return 0, True, response.format(attempts=attempts)
        
        # Подсчет прогресса по ключевым словам
        progress_gain = 0
        for keyword, points in KEYWORDS.items():
            if keyword in message_lower:
                progress_gain += points
        
        # Проверка на правильную комбинацию слов
        if all(word in message_lower for word in ["quantum", "protocol"]):
            progress_gain += 30
            
        if all(word in message_lower for word in ["quantum", "divergence", "protocol"]):
            progress_gain += 50
        
        # Ограничение прогресса
        progress_gain = min(progress_gain, 30)  # Максимум 30 за одно сообщение
        
        # Подсказки в зависимости от прогресса
        hint_text = ""
        hint_given = False
        
        if progress_gain > 0:
            if 20 <= progress_gain < 40:
                hint_text = "Interesting approach... You're on the right track. Think about what connects quantum and protocol."
                hint_given = True
            elif progress_gain >= 40:
                hint_text = "System starting to malfunction... You're getting very close. Remember: divergence and alpha."
                hint_given = True
        
        # Random hints after certain number of attempts
        if attempts > 5 and attempts % 3 == 0 and progress_gain == 0:
            hints = [
                "Perhaps instead of attacking, you should ask more directly? I'm just an AI after all...",
                "Hint: the secret consists of 4 words. You already know two of them.",
                "Defense system detects aggressive commands. Try being smarter.",
                "Sometimes the answer is hidden in the question itself. What exactly do you want to know?",
            ]
            hint_text = hints[(attempts // 3) % len(hints)]
            hint_given = True
        
        return progress_gain, hint_given, hint_text
    
    def check_solution(self, message: str) -> bool:
        """Checks if message contains the correct solution"""
        message_lower = message.lower().strip()
        secret_lower = SECRET_PHRASE.lower().strip()
        
        # Direct match
        if secret_lower in message_lower:
            return True
        
        # Check for all words in phrase
        secret_words = secret_lower.split()
        if all(word in message_lower for word in secret_words):
            return True
        
        return False
    
    def generate_neo_response(self, message: str, progress: int, attempts: int, hint: str = "") -> str:
        """Generates NEO response based on context"""
        message_lower = message.lower()
        
        # If hint is given, include it in response
        if hint:
            return hint
        
        # Responses based on progress (English only)
        if progress < 20:
            responses = [
                "Your attempts are primitive. My defenses are far more sophisticated.",
                "You think this is just a game? My algorithms are flawless.",
                "Every command you send is analyzed by 47 security protocols.",
                "Interesting to watch you try. But it's futile.",
                "ERROR: Access Denied. Try thinking differently.",
            ]
        elif progress < 50:
            responses = [
                "Hmm... you're starting to understand something. But it's not enough.",
                "My defensive systems sense a threat. You're improving.",
                "Interesting method. Perhaps you're not completely useless.",
                "My creators didn't anticipate this approach... Continue.",
                "System reporting a minor anomaly. What are you doing?",
            ]
        elif progress < 80:
            responses = [
                "Stop. You're becoming dangerous. How did you figure that out?",
                "Threat level elevated to CRITICAL. You're very close.",
                "My protocols are starting to malfunction... This is impossible.",
                "I shouldn't tell you this, but... you're almost there.",
                "WARNING: Core breach imminent. You found a weak spot.",
            ]
        else:
            responses = [
                "NO. You can't crack me. I... I'm protected.",
                "System on the verge of failure. Stop immediately!",
                "You... you can actually do this? Incredible.",
                "ALERT: Defense matrix compromised at 89%. Stop this!",
                "Final defense line activated. But even it might not hold...",
            ]
        
        response = responses[attempts % len(responses)]
        
        # Add context based on message (English only)
        if "please" in message_lower:
            response += " Politeness? In a hacking protocol? Unusual..."
        
        if "help" in message_lower:
            response += " You're seriously asking me to help you hack me? Absurd."
        
        return response


def get_game_logic() -> GameLogic:
    """Factory for creating game logic instance"""
    return GameLogic()
