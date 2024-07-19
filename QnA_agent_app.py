import os
from flask import Flask, request, jsonify
import openai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from PyPDF2 import PdfReader
import json

app = Flask(__name__)

# CREATE PDF EXTRACTOR CLASS
class PDFExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    # Read the pdf line by line and extract the text into a single string
    def extract_text(self):
        print(f"Extracting text from PDF: {self.pdf_path}")
        reader = PdfReader(self.pdf_path)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
        print(f"Extracted text length: {len(text)}")
        return text

# CREATE QUESTION PROCESSOR CLASS
# OPENAI MODEL CANNOT ANSWER THE QUESTIONS FROM THE ENTIRE TEXT IN ONE GO SO WE NEED A CLASS WHICH CAN CHUNK THE DOCUMENT
# ASK QUESTIONS ON EACH CHUNK AND THEN COMBINE ANSWERS FROM EACH CHUNK TO RETURN THE FINAL ANSWER
class QuestionProcessor:
    def __init__(self, openai_api_key):
        openai.api_key = openai_api_key
        print("OpenAI API key set")

    # SPLIT THE TEXT IN SMALL MANAGABLE CHUNKS
    def split_text_into_chunks(self, text, max_tokens=3500):
        print("Splitting text into chunks")
        words = text.split()
        chunks = []
        current_chunk = []
        current_chunk_token_count = 0

        for word in words:
            word_token_count = len(word.split())
            if current_chunk_token_count + word_token_count > max_tokens:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_chunk_token_count = word_token_count
            else:
                current_chunk.append(word)
                current_chunk_token_count += word_token_count

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        print(f"Created {len(chunks)} chunks")
        return chunks

    # ASK QUESTION BASED ON A SINGLE CHUNK
    def ask_question_on_chunk(self, chunk, question):
        print(f"Asking question on chunk: {chunk[:50]}...")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Based on the following document chunk, answer the question verbatim, : '{question}'\n\nDocument Chunk:\n{chunk}"}
            ],
            max_tokens=1500,
            n=1,
            stop=None,
            temperature=0.5,
        )
        print("Received response for chunk")
        return response['choices'][0]['message']['content'].strip()

    # COMBINE ANSWERS FROM ALL CHUNKS INTO A SINGLE ANSWER
    def ask_question_on_text(self, text, question):
        chunks = self.split_text_into_chunks(text)

        responses = []
        for chunk in chunks:
            response = self.ask_question_on_chunk(chunk, question)
            responses.append(response)

        combined_response = " ".join(responses)
        print(f"Combined response length: {len(combined_response)}")

        summary = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Find the Answer to the following question from these responses, combine the information from all the sentences to find the correct answer: '{question}'\n\nQuestion sentences:\n{combined_response}"}

            ],
            max_tokens=3500,
            n=1,
            stop=None,
            temperature=0.5,
        )
        final_answer = summary['choices'][0]['message']['content'].strip()
        
  
        return final_answer

    # ONLY ANSWER THE QUESTION IF ANSWER IS AVAILABLE
    def ask_questions(self, pdf_text, questions):
        answers = {}
        for question in questions:
            print(f"Asking question: {question}")
            try:
                answer = self.ask_question_on_text(pdf_text, question)
                if self.is_low_confidence(answer):
                    answers[question] = "Data Not Available"
                else:
                    answers[question] = answer
            except Exception as e:
                print(f"Error asking question '{question}': {str(e)}")
                answers[question] = "Data Not Available"
        return answers

    def is_low_confidence(self, answer):
        low_confidence_indicators = [ "do not provide", "does not contain",
            "sorry",  "no information", "no data", "data not available",
             "no answer", "unknown", "no details", "insufficient",
            "no record", "no mention", "no reference", "no clue", "no hint", "no context",
            "no explanation", "no insight", "no specifics", "no particular", "no information available"
        ]
        answer_lower = answer.lower()

        for indicator in low_confidence_indicators:
            if indicator in answer_lower:
                return True

        return False


# CREATE SLACK NOTIFIER CLASS
class SlackNotifier:
    def __init__(self, slack_token, slack_channel):
        self.slack_client = WebClient(token=slack_token)
        self.slack_channel = slack_channel
        print("Slack client initialized")

    def post_message(self, message):
        try:
            response = self.slack_client.chat_postMessage(channel=self.slack_channel, text=message)
            print(f"Message posted to Slack: {response}")
        except SlackApiError as e:
            error_message = e.response['error']
            print(f"Error posting to Slack: {error_message}")

# CREATE QnA AGENT CLASS
class QnA_Agent:
    def __init__(self, pdf_path, openai_api_key, slack_token, slack_channel):
        print("Initializing QnA Agent")
        self.pdf_extractor = PDFExtractor(pdf_path)
        self.question_processor = QuestionProcessor(openai_api_key)
        self.slack_notifier = SlackNotifier(slack_token, slack_channel)

    def process_and_notify(self, questions):
        print("Extracting text from PDF")
        pdf_text = self.pdf_extractor.extract_text()

        print("Getting answers to questions")
        answers = self.question_processor.ask_questions(pdf_text, questions)

        formatted_answers = json.dumps(answers, indent=2)

        print("Posting answers to Slack...")
        self.slack_notifier.post_message(f"Answers to your questions:\n```{formatted_answers}```")

@app.route('/process', methods=['POST'])
def process_pdf():
    data = request.form
    openai_api_key = data['openai_api_key']
    slack_token = data['slack_token']
    slack_channel = data['slack_channel']
    questions = json.loads(data['questions'])
    
    pdf_file = request.files['pdf']
    pdf_path = os.path.join("/tmp", pdf_file.filename)
    pdf_file.save(pdf_path)

    print(f"PDF saved to: {pdf_path}")

    qna_agent = QnA_Agent(pdf_path, openai_api_key, slack_token, slack_channel)
    qna_agent.process_and_notify(questions)

    return jsonify({"status": "success", "message": "Processing completed and message posted to Slack."})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
