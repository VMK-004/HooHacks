from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount
import json
import re
from pathlib import Path
from google import genai
import os
from dotenv import load_dotenv

class EduVerseBot(ActivityHandler):
    def __init__(self):
        super().__init__()
        print("Initializing EduVerseBot...")
        self.knowledge_base = self._load_knowledge_base()
        self.conversation_history = {}

        # Load environment variables
        load_dotenv()

        # Initializing Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables")
        else:
            self.genai_client = genai.Client(api_key=api_key)
        
    async def _generate_gemini_response(self, user_message, user_id):
        system_prompt = """You are Edura, an AI educational mentor for EduVerse. 
        You help users with project suggestions, career guidance, course recommendations, 
        code review, and general educational questions. Maintain a helpful, encouraging tone.
        Your responses should be educational and guide users toward learning resources."""
        
        history = self.conversation_history.get(user_id, [])
        recent_history = history[-5:] if len(history) > 5 else history
        
        conversation_context = ""
        for interaction in recent_history:
            conversation_context += f"User: {interaction['user_message']}\n"
            conversation_context += f"Edura: {interaction['bot_response']}\n"
        
        project_data = ""
        tech_keywords = {
            'python': 'python_projects',
            'java': 'java_projects',
            'node': 'node_projects',
            'javascript': 'node_projects',
            'react': 'react_projects',
            'sql': 'sql_projects',
            'database': 'sql_projects'
        }
        for keyword, data_key in tech_keywords.items():
            if keyword in user_message.lower() and data_key in self.knowledge_base:
                project_data += f"\n\n{keyword.upper()} PROJECTS DATA:\n"
                project_data += json.dumps(self.knowledge_base[data_key][:3], indent=2)
        
        prompt = f"{system_prompt}\n\n{project_data}\n\nConversation History:\n{conversation_context}\n\nUser: {user_message}\nEdura:"
        print(prompt)
        try:
            response = self.genai_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {str(e)}")
            return "I'm having trouble connecting to my knowledge systems. Let's try a different approach to your question."

    def _load_knowledge_base(self):
        kb = {}
        try:
            with open('ai/knowledge_base.json', 'r') as f:
                kb = json.load(f)
        except FileNotFoundError:
            kb = {
                'faqs': {
                    'how to start': 'Start by choosing a learning path and completing the skill assessment',
                    'pricing': 'We offer both free and premium plans. Check our pricing page for details',
                    'certificates': 'Yes, you receive certificates upon completing courses',
                    'learning paths': 'We offer structured learning paths in Web Development, Data Science, and Mobile Development',
                    'support': 'You can reach our support team 24/7 through chat or email at support@eduverse.com'
                },
                'career_paths': {
                    'web development': {
                        'roles': ['Frontend Developer', 'Backend Developer', 'Full Stack Developer'],
                        'skills': ['HTML/CSS', 'JavaScript', 'React/Angular', 'Node.js', 'Databases'],
                        'courses': ['Web Development Bootcamp', 'JavaScript Mastery', 'React Complete Guide']
                    },
                    'data science': {
                        'roles': ['Data Analyst', 'Machine Learning Engineer', 'Data Scientist'],
                        'skills': ['Python', 'SQL', 'Machine Learning', 'Statistics', 'Data Visualization'],
                        'courses': ['Data Science Fundamentals', 'Machine Learning A-Z', 'Python for Data Science']
                    }
                },
                'project_suggestions': {
                    'web': [
                        {'name': 'Portfolio Website', 'difficulty': 'Beginner'},
                        {'name': 'E-commerce Platform', 'difficulty': 'Intermediate'},
                        {'name': 'Social Media Clone', 'difficulty': 'Advanced'}
                    ],
                    'python': [
                        {'name': 'Web Scraper', 'difficulty': 'Beginner'},
                        {'name': 'Task Management API', 'difficulty': 'Intermediate'},
                        {'name': 'Data Analysis Dashboard', 'difficulty': 'Advanced'}
                    ]
                },
                'courses': {},
                'learning_data': []
            }
        
        project_files = [
            ('python_projects_complete.json', 'python_projects'),
            ('java_projects_complete.json', 'java_projects'),
            ('node_projects_complete.json', 'node_projects'),
            ('react_projects_complete.json', 'react_projects'),
            ('sql_projects_complete.json', 'sql_projects')
        ]
        for file_name, key_name in project_files:
            try:
                with open(f'frontend/src/Notes/{file_name}', 'r') as f:
                    kb[key_name] = json.load(f)
                    print(f"Loaded {file_name} successfully")
            except FileNotFoundError:
                print(f"Warning: {file_name} not found")
        
        return kb

    async def _save_interaction(self, user_id, user_message, bot_response):
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        self.conversation_history[user_id].append({
            'user_message': user_message,
            'bot_response': bot_response
        })
        self.knowledge_base['learning_data'].append({
            'input': user_message,
            'response': bot_response
        })
        with open('ai/knowledge_base.json', 'w') as f:
            json.dump(self.knowledge_base, f)

    async def _analyze_code(self, code):
        suggestions = []
        if 'print' in code and not any(['def' in code, 'class' in code]):
            suggestions.append("Consider wrapping this code in a function for better reusability")
        if not code.strip().startswith('def') and len(code.split('\n')) > 5:
            suggestions.append("Consider breaking this code into smaller functions")
        return suggestions

    async def on_message_activity(self, turn_context: TurnContext):
        user_id = turn_context.activity.from_property.id
        user_message = turn_context.activity.text.lower()
        response = ""

        code_pattern = re.compile(r'``````')
        if code_match := code_pattern.search(user_message):
            code = code_match.group(0).strip('`')
            suggestions = await self._analyze_code(code)
            response = "Code Analysis Results:\n" + "\n".join(suggestions)
        elif "project" in user_message:
            tech_mapping = {
                'python': 'python_projects',
                'java': 'java_projects', 
                'node': 'node_projects',
                'javascript': 'node_projects',
                'react': 'react_projects',
                'sql': 'sql_projects',
                'database': 'sql_projects'
            }
            detected_tech = next((tech for tech in tech_mapping.keys() if tech in user_message), None)
            if detected_tech and tech_mapping[detected_tech] in self.knowledge_base:
                response = await self._generate_gemini_response(user_message, user_id)
            elif detected_tech:
                response = f"I don't have detailed {detected_tech} project data, but here are some general suggestions..."
            else:
                response = "I can suggest projects in various technologies. What interests you? (Python, Java, Node.js, React, SQL)"
        elif "career" in user_message:
            career_type = next((career for career in ['web development', 'data science'] 
                            if career in user_message), None)
            if career_type and career_type in self.knowledge_base['career_paths']:
                career_info = self.knowledge_base['career_paths'][career_type]
                response = f"For a career in {career_type.title()}, here's what you need to know:\n\n"
                response += f"Potential Roles:\n{', '.join(career_info['roles'])}\n\n"
                response += f"Key Skills:\n{', '.join(career_info['skills'])}\n\n"
                response += f"Recommended Courses:\n{', '.join(career_info['courses'])}"
            else:
                response = "I can provide career guidance in various tech fields. What area interests you?"
        elif "course" in user_message:
            if "beginner" in user_message:
                response = "For beginners, I recommend:\n1. CS50 by Harvard\n2. Python for Everybody\n3. Web Development Bootcamp"
            else:
                response = "What's your current skill level and area of interest? This will help me suggest appropriate courses."
        elif "faq" in user_message:
            faqs = {
                "how to start": "Start by choosing a learning path and completing the skill assessment",
                "pricing": "We offer both free and premium plans. Check our pricing page for details",
                "certificates": "Yes, you receive certificates upon completing courses"
            }
            for keyword, answer in faqs.items():
                if keyword in user_message:
                    response = answer
                    break
            if not response:
                response = "Browse our comprehensive FAQ section at: [EduVerse FAQs](#)"
        else:
            response = await self._generate_gemini_response(user_message, user_id)

        await turn_context.send_activity(response)
        await self._save_interaction(user_id, user_message, response)

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    "Welcome to EduVerse! I'm Edura, your AI mentor. I can help you with:\n"
                    "1. Project suggestions\n"
                    "2. Career guidance\n"
                    "3. Course recommendations\n"
                    "4. Code review\n"
                    "5. FAQs\n"
                    "How can I assist you today?"
                )
