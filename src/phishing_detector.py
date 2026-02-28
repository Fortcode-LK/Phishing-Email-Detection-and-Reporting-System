import asyncio
import re
import os
from email import message_from_bytes, policy
from email.parser import BytesParser
from aiosmtpd.controller import Controller
import joblib
from pathlib import Path
from bs4 import BeautifulSoup, Comment
import html

class PhishingDetector:
    
    def __init__(self, host='localhost', port=1025, model_dir=None, whitelist_domains=None):
        self.host = host
        self.port = port
        
        if model_dir is None:
            base_dir = Path(__file__).parent.parent
            model_dir = base_dir / 'models' / 'model b' / 'trainning2'
        
        model_dir = Path(model_dir)
        self.model_path = model_dir / 'phishing_model_b.joblib'
        self.vectorizer_path = model_dir / 'tfidf_vectorizer_b.joblib'
        
        print(f"Loading model from: {self.model_path}")
        print(f"Loading vectorizer from: {self.vectorizer_path}")
        self.model = joblib.load(self.model_path)
        self.vectorizer = joblib.load(self.vectorizer_path)
        print("Model and vectorizer loaded successfully!")
        
        if whitelist_domains is None:
            self.whitelist_domains = {
                'google.com',
                'accounts.google.com',
                'gmail.com',
                'redditmail.com',
                'reddit.com',
                'github.com',
                'microsoft.com',
                'amazon.com',
                'paypal.com',
                'apple.com',
                'linkedin.com',
                'twitter.com',
                'facebook.com',
                'instagram.com',
            }
        else:
            self.whitelist_domains = set(whitelist_domains)
        
        print(f"Whitelisted domains: {len(self.whitelist_domains)} trusted senders")
        
        self.smtp_controller = None
    
    async def handle_DATA(self, server, session, envelope):
        print(f"\n{'='*60}")
        print(f"Received email from: {envelope.mail_from}")
        print(f"Recipients: {envelope.rcpt_tos}")
        print(f"{'='*60}")
        
        try:
            email_content = envelope.content
            
            extracted_data = self.preprocess_email(email_content)
            
            if extracted_data:
                sender = envelope.mail_from
                subject = extracted_data['subject']
                body = extracted_data['body']
                original_sender = extracted_data.get('original_sender')
                
                print(f"\n[PREPROCESSING RESULTS]")
                print(f"Original Subject: {extracted_data['original_subject'][:100]}")
                print(f"Cleaned Subject: {subject[:100]}")
                print(f"\nOriginal Body (first 300 chars):")
                print(f"{extracted_data['original_body'][:300]}")
                print(f"\nCleaned Body (first 300 chars):")
                print(f"{body[:300]}")
                print(f"\nBody length: {len(body)} characters")
                
                if original_sender:
                    print(f"\n[ORIGINAL SENDER DETECTED]")
                    print(f"Original sender: {original_sender}")
                
                if len(body) < 20:
                    print(f"\nΓÜá WARNING: Body too short after cleaning - may indicate preprocessing issue")
                
# Check both the direct SMTP sender and any detected forwarded
                # original sender against the whitelist.
                whitelisted_address = None
                if self.is_whitelisted(sender):
                    whitelisted_address = sender
                elif original_sender and self.is_whitelisted(original_sender):
                    whitelisted_address = original_sender

                if whitelisted_address:
                    print(f"\n[WHITELIST CHECK]")
                    print(f"✔ Domain whitelisted ({whitelisted_address}) - skipping model")
                    result = {
                        'label': 'legitimate',
                        'probability': 1.0,
                        'reason': 'whitelisted_domain'
                    }
                else:
                    if original_sender:
                        print(f"\n[WHITELIST CHECK]")
                        print(f"✘ Domain not whitelisted - running model")
                    
                    result = self.classify_email(subject, body)
                    result['reason'] = 'model_prediction'
                
                print(f"\n{'='*60}")
                print(f"CLASSIFICATION RESULT:")
                print(f"  Sender: {sender}")
                if original_sender:
                    print(f"  Original Sender: {original_sender}")
                print(f"  Label: {result['label'].upper()}")
                print(f"  Probability: {result['probability']:.2%}")
                print(f"  Reason: {result['reason']}")
                print(f"{'='*60}\n")
                
            else:
                print("Failed to extract email content")
                
        except Exception as e:
            print(f"Error processing email: {e}")
            import traceback
            traceback.print_exc()
        
        return '250 Message accepted for delivery'
    
    def start_server(self):
        handler = SMTPHandler(self)
        self.smtp_controller = Controller(
            handler, 
            hostname=self.host, 
            port=self.port
        )
        self.smtp_controller.start()
        print(f"\nSMTP Server started on {self.host}:{self.port}")
        print(f"Waiting for emails... (Press Ctrl+C to stop)\n")
    
    def stop_server(self):
        if self.smtp_controller:
            self.smtp_controller.stop()
            print("SMTP Server stopped")
    
    def get_original_sender(self, raw_body, email_msg=None):
        patterns = [
            r'from[:\s]+<?([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})>?',
            r'forwarded\s+(?:message\s+)?from[:\s]+<?([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})>?',
            r'originally\s+sent\s+by[:\s]+<?([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})>?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, raw_body, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        
        if email_msg:
            original_from = email_msg.get('X-Original-From', '')
            if original_from:
                email_match = re.search(r'([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})', original_from, re.IGNORECASE)
                if email_match:
                    return email_match.group(1).lower()
            
            in_reply_to = email_msg.get('In-Reply-To', '')
            if in_reply_to:
                email_match = re.search(r'([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})', in_reply_to, re.IGNORECASE)
                if email_match:
                    return email_match.group(1).lower()
        
        return None
    
    def is_whitelisted(self, email_address):
        if not email_address or '@' not in email_address:
            return False
        
        domain = email_address.split('@')[-1].lower()
        
        if domain in self.whitelist_domains:
            return True
        
        parts = domain.split('.')
        if len(parts) > 2:
            parent_domain = '.'.join(parts[-2:])
            if parent_domain in self.whitelist_domains:
                return True
        
        return False
    
    def preprocess_email(self, raw_email):
        try:
            if isinstance(raw_email, bytes):
                msg = message_from_bytes(raw_email, policy=policy.default)
            else:
                msg = message_from_bytes(raw_email.encode(), policy=policy.default)
            
            subject = msg.get('subject', '')
            
            body = self._extract_body(msg)
            
            body = self._remove_invisible_unicode(body)
            
            original_sender = self.get_original_sender(body, msg)
            
            original_subject, original_body = self._extract_forwarded_content(subject, body)
            
            cleaned_subject = self._clean_text(original_subject)
            cleaned_body = self._clean_text(original_body)
            
            return {
                'subject': cleaned_subject,
                'body': cleaned_body,
                'original_subject': subject,
                'original_body': body,
                'original_sender': original_sender
            }
            
        except Exception as e:
            print(f"Error parsing email: {e}")
            return None
    
    def _remove_invisible_unicode(self, text):
        if not text:
            return ""
        
        text = html.unescape(text)
        
        text = re.sub(r'(\S)\u00AD(\S)', r'\1 \2', text)
        text = text.replace('\u00AD', '')
        
        text = text.replace('\u200B', ' ')
        text = text.replace('\u200C', ' ')
        text = text.replace('\u200D', ' ')
        text = text.replace('\uFEFF', ' ')
        
        text = re.sub(r'[\u200e\u200f\u202a-\u202e\u2060\u180e\u061c]', ' ', text)
        
        text = text.replace('\u00A0', ' ')
        text = text.replace('\u2002', ' ')
        text = text.replace('\u2003', ' ')
        text = text.replace('\u2009', ' ')
        text = text.replace('\u200A', ' ')
        text = text.replace('\u202F', ' ')
        
        text = re.sub(r'[\u0300-\u036f\u0483-\u0489\u034f\u115f\u1160]', '', text)
        
        text = re.sub(r'  +', ' ', text)
        
        return text
    
    def _extract_body(self, msg):
        body = ""
        html_body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                if 'attachment' in content_disposition:
                    continue
                
                if content_type == 'text/plain':
                    try:
                        body = part.get_content()
                    except:
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            body = str(part.get_payload())
                    
                    if body and len(body.strip()) > 50:
                        break
                
                elif content_type == 'text/html' and not html_body:
                    try:
                        html_body = part.get_content()
                    except:
                        try:
                            html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            html_body = str(part.get_payload())
        else:
            content_type = msg.get_content_type()
            if content_type == 'text/plain':
                try:
                    body = msg.get_content()
                except:
                    body = str(msg.get_payload(decode=True))
            elif content_type == 'text/html':
                try:
                    html_body = msg.get_content()
                except:
                    html_body = str(msg.get_payload(decode=True))
        
        if not body and html_body:
            body = self._html_to_text(html_body)
        
        body = self._remove_email_artifacts(body)
        
        return body if body else ""
    
    def _remove_email_artifacts(self, text):
        if not text:
            return ""
        
        text = re.sub(r'^\s*(?:To|From|Date|Sent|Cc|Bcc|Subject|Reply-To):\s*.+?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        text = re.sub(r'^On\s+.+?wrote:\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        text = re.sub(r'^[>|]\s*.+?$', '', text, flags=re.MULTILINE)
        
        text = re.sub(r'style\s*=\s*["\'][^"\']{0,200}["\']', ' ', text, flags=re.IGNORECASE)
        
        text = re.sub(r'@media[^{]*\{[^}]*\}', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'@[a-z-]+\s+[^{]*\{[^}]*\}', ' ', text, flags=re.IGNORECASE)
        
        text = re.sub(r'class\s*=\s*["\'][^"\']+["\']', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'id\s*=\s*["\'][^"\']+["\']', ' ', text, flags=re.IGNORECASE)
        
        text = re.sub(r'data:image/[^;]+;base64,[^\s]+', '', text)
        text = re.sub(r'https?://[^\s]*\.(?:png|jpg|gif|jpeg)\?[^\s]*', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'--\s*\w+\s*(?:boundary|delimiter)\s*--', ' ', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()
    
    def _html_to_text(self, html_content):
        if not html_content:
            return ""
        
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            for script in soup(["script", "style", "head", "meta", "link"]):
                script.decompose()
            
            for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
                comment.extract()
            
            text = soup.get_text(separator=' ')
            
            text = html.unescape(text)
            
            return text
            
        except Exception as e:
            print(f"Warning: BeautifulSoup parsing failed, using regex fallback: {e}")
            return self._html_to_text_fallback(html_content)
    
    def _html_to_text_fallback(self, html_content):
        if not html_content:
            return ""
        
        html_content = re.sub(r'<script[^>]*>.*?</script>', ' ', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        html_content = re.sub(r'<style[^>]*>.*?</style>', ' ', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        html_content = re.sub(r'<head[^>]*>.*?</head>', ' ', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        html_content = re.sub(r'<!--.*?-->', ' ', html_content, flags=re.DOTALL)
        
        html_content = re.sub(r'</(div|p|br|tr|h[1-6]|li)[^>]*>', '\n', html_content, flags=re.IGNORECASE)
        
        html_content = re.sub(r'<[^>]+>', ' ', html_content)
        
        text = html.unescape(html_content)
        
        return text
    
    def _extract_forwarded_content(self, subject, body):
        original_subject = subject
        if subject.lower().startswith('fwd:'):
            original_subject = subject[4:].strip()
        elif subject.lower().startswith('fw:'):
            original_subject = subject[3:].strip()
        
        original_body = body
        
        header_pattern = r'(?:From|FROM):\s*.+?(?:\n|\r\n)(?:.*?\n)*?(?:Subject|SUBJECT):\s*(.+?)(?:\n|\r\n)(.+)'
        match = re.search(header_pattern, body, re.DOTALL | re.IGNORECASE)
        
        if match:
            forwarded_subject = match.group(1).strip()
            content_after_headers = match.group(2)
            
            if not original_subject or original_subject.lower() in body.lower():
                original_subject = forwarded_subject
            
            original_body = self._clean_forwarded_body(content_after_headers)
        else:
            forwarding_markers = [
                '---------- Forwarded message ---------',
                '---------- Forwarded message ----------',
                '------- Forwarded message -------',
                'Begin forwarded message:',
                'Forwarded by Gmail',
                '----Original Message----',
                '-----Original Message-----',
                '--- Forwarded message ---',
            ]
            
            marker_found = False
            for marker in forwarding_markers:
                if marker in body:
                    parts = body.split(marker, 1)
                    if len(parts) > 1:
                        forwarded_content = parts[1]
                        
                        subject_match = re.search(r'\n\s*Subject:\s*(.+?)(?:\n|$)', forwarded_content, re.IGNORECASE)
                        if subject_match:
                            start_idx = subject_match.end()
                            remaining = forwarded_content[start_idx:]
                            original_body = self._clean_forwarded_body(remaining)
                            marker_found = True
                            break
            
            if not marker_found:
                original_body = self._clean_forwarded_body(body)
        
        return original_subject, original_body
    
    def _clean_forwarded_body(self, text):
        if not text:
            return ""
        
        text = re.sub(r'^\s*(To|From|Date|Sent|Cc|Bcc|Subject|Reply-To|Delivered-To|Return-Path):\s*.+?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        text = re.sub(r'^On\s+.+?wrote:\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        text = self._remove_signatures(text)
        
        text = re.sub(r'https?://[^\s]+\.(?:png|jpg|gif|jpeg|svg)\?[^\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'https?://[^\s]*(?:track|click|pixel|beacon|analytics|utm_)[^\s]*', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'data:image/[^;]+;base64,[^\s]+', '', text)
        
        text = re.sub(r'(?:view|read|open).{0,30}(?:browser|web|online)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(?:unsubscribe|manage\s+preferences|update\s+settings)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(?:click\s+here|tap\s+here|learn\s+more)', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'r/[a-z0-9_]+:', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'subscribe\s+to\s+our\s+newsletter', '', text, flags=re.IGNORECASE)
        text = re.sub(r'follow\s+us\s+on', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'={3,}', '', text)
        text = re.sub(r'[-_]{5,}', ' ', text)
        
        text = re.sub(r'^\s*Sent from my .+$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'^\s*Get Outlook for .+$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        text = re.sub(r'^[>|]\s*.+?$', '', text, flags=re.MULTILINE)
        
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def _remove_signatures(self, text):
        signature_patterns = [
            r'\n--\s*\n.*$',
            r'\n_{10,}.*$',
            r'\n={10,}.*$',
            r'\nBest regards.*$',
            r'\nThanks.*$',
            r'\nSent from.*$',
        ]
        
        for pattern in signature_patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
        
        return text.strip()
    
    def _clean_text(self, text):
        if not text:
            return ""
        
        text = html.unescape(text)
        
        text = re.sub(r'&[a-z]+;', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'&#\d+;', ' ', text)
        text = re.sub(r'&#x[0-9a-f]+;', ' ', text, flags=re.IGNORECASE)
        
        text = text.replace('\u200B', ' ')
        text = text.replace('\u200C', ' ')
        text = text.replace('\u200D', ' ')
        text = re.sub(r'[\u200e\u200f\u202a-\u202e\u2060\uFEFF\u180e\u061c]', ' ', text)
        
        text = re.sub(r'(\S)\u00AD(\S)', r'\1 \2', text)
        text = text.replace('\u00AD', ' ')
        
        text = text.replace('\u00A0', ' ')
        text = re.sub(r'[\u2002\u2003\u2009\u200A\u202F]', ' ', text)
        
        text = re.sub(r'[\u0300-\u036f\u0483-\u0489\u0591-\u05bd\u05bf\u05c1\u05c2\u05c4\u05c5\u05c7]', '', text)
        text = re.sub(r'[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06dc\u06df-\u06e4\u06e7\u06e8]', '', text)
        text = re.sub(r'[\u06ea-\u06ed\u0711\u0730-\u074a\u07a6-\u07b0\u07eb-\u07f3]', '', text)
        
        text = re.sub(r'[\u034f\u115f\u1160\u17b4\u17b5\u180b-\u180d]', '', text)
        
        text = re.sub(r'\w+\s*\{[^}]+\}', ' ', text)
        text = re.sub(r'sup\s*\{[^}]+\}', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'[a-z-]+\s*:\s*[^;{}\n]+\s*!important\s*;?', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'[a-z-]+\s*:\s*[^;{}\n]+;', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'[{}!;%@#~^*]', ' ', text)

        text = re.sub(r'\br/[a-z0-9_]+\b\s*:?\s*', ' ', text, flags=re.IGNORECASE)
        
        text = re.sub(r'(?:view|read|open)\s+(?:this\s+)?(?:email|message|newsletter)\s+(?:in|on)\s+(?:your\s+)?(?:browser|web)', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'(?:unsubscribe|manage\s+preferences|update\s+email|update\s+settings)', ' ', text, flags=re.IGNORECASE)
        
        text = re.sub(r'https?://[^\s]+\?[^\s]+', ' ', text)
        text = re.sub(r'https?://[^\s]*(?:track|pixel|beacon|analytics|click)[^\s]*', ' ', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b', ' ', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\b[a-f0-9]{32,}\b', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'\b[A-Za-z0-9+/]{40,}={0,2}\b', ' ', text)
        
        text = re.sub(r'[_=\-|\\\/]{3,}', ' ', text)
        text = re.sub(r'\.{3,}', ' ', text)
        
        text = re.sub(r'sent\s+from\s+my\s+\w+', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'on\s+.+?wrote:', ' ', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\b\d{10,}\b', ' ', text)
        
        text = text.lower()
        
        text = re.sub(r'\s+', ' ', text)
        
        text = text.strip()
        
        words = text.split()
        meaningful_chars = {'i', 'a'}
        words = [w for w in words if len(w) > 1 or w in meaningful_chars]
        text = ' '.join(words)
        
        if len(text) < 5:
            return ""
        
        words = text.split()
        if len(words) < 2:
            return ""
        
        return text
    
    def classify_email(self, subject, body):
        text = f"{subject} {body}"
        
        features = self.vectorizer.transform([text])
        
        prediction = self.model.predict(features)[0]
        prediction_proba = self.model.predict_proba(features)[0]
        
        probability = prediction_proba[prediction]
        
        label = 'phishing' if prediction == 1 else 'legitimate'
        
        return {
            'label': label,
            'probability': float(probability)
        }

class SMTPHandler:
    
    def __init__(self, detector):
        self.detector = detector
    
    async def handle_DATA(self, server, session, envelope):
        return await self.detector.handle_DATA(server, session, envelope)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Phishing Email Detection System')
    parser.add_argument('--host', default='localhost', help='SMTP server host (default: localhost)')
    parser.add_argument('--port', type=int, default=1025, help='SMTP server port (default: 1025)')
    parser.add_argument('--model-dir', default=None, help='Directory containing model files')
    parser.add_argument('--whitelist', nargs='*', help='Additional domains to whitelist (e.g., mycompany.com)')
    parser.add_argument('--no-whitelist', action='store_true', help='Disable domain whitelisting')
    
    args = parser.parse_args()
    
    try:
        whitelist_domains = None
        if args.no_whitelist:
            whitelist_domains = set()
            print("Domain whitelisting disabled")
        elif args.whitelist:
            whitelist_domains = {
                'google.com', 'gmail.com', 'redditmail.com', 'reddit.com',
                'github.com', 'microsoft.com', 'amazon.com', 'paypal.com',
                'apple.com', 'linkedin.com', 'twitter.com', 'facebook.com'
            }
            for domain in args.whitelist:
                whitelist_domains.add(domain.lower())
                print(f"Added to whitelist: {domain}")
        
        detector = PhishingDetector(
            host=args.host,
            port=args.port,
            model_dir=args.model_dir,
            whitelist_domains=whitelist_domains
        )
        
        detector.start_server()
        
        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
            detector.stop_server()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

