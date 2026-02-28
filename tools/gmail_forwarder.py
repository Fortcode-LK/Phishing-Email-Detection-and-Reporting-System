import imaplib
import email
import smtplib
from email import policy
from email.parser import BytesParser
import getpass
import sys

def fetch_and_forward_gmail(gmail_user, gmail_password, 
                            smtp_host='localhost', smtp_port=1025,
                            folder='INBOX', limit=5, search_criteria='ALL'):
    
    print(f"Connecting to Gmail IMAP server...")
    
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(gmail_user, gmail_password)
        print(f"✓ Successfully logged in as {gmail_user}")
        
        mail.select(folder)
        print(f"✓ Selected folder: {folder}")
        
        status, messages = mail.search(None, search_criteria)
        email_ids = messages[0].split()
        
        if not email_ids:
            print(f"\n✗ No emails found matching criteria: {search_criteria}")
            mail.close()
            mail.logout()
            return
        
        email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
        print(f"Found {len(email_ids)} email(s) to process\n")
        
        for i, email_id in enumerate(email_ids, 1):
            print(f"{'-'*70}")
            print(f"Processing email {i}/{len(email_ids)}...")
            print(f"{'-'*70}")
            
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            raw_email = msg_data[0][1]
            
            msg = email.message_from_bytes(raw_email, policy=policy.default)
            
            print(f"From: {msg['From']}")
            print(f"Subject: {msg['Subject']}")
            print(f"Date: {msg['Date']}")
            
            try:
                with smtplib.SMTP(smtp_host, smtp_port) as smtp:
                    smtp.send_message(msg)
                    print(f"✓ Forwarded to {smtp_host}:{smtp_port}")
            except Exception as e:
                print(f"✗ Failed to forward: {e}")
            
            print()
        
        mail.close()
        mail.logout()
        print(f"\n{'='*70}")
        print(f"Done! Processed {len(email_ids)} email(s)")
        print(f"Check the phishing detector terminal for classification results.")
        print(f"{'='*70}\n")
        
    except imaplib.IMAP4.error as e:
        print(f"\n✗ Gmail IMAP error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're using an App Password, not your regular Gmail password")
        print("2. Enable IMAP in Gmail Settings → Forwarding and POP/IMAP")
        print("3. Create an App Password at: https://myaccount.google.com/apppasswords")
        print()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

def send_raw_email_to_localhost(raw_email_text, smtp_host='localhost', smtp_port=1025):
    try:
        msg = email.message_from_string(raw_email_text, policy=policy.default)
        
        print(f"\nParsed Email:")
        print(f"  From: {msg['From']}")
        print(f"  Subject: {msg['Subject']}")
        print(f"  Date: {msg['Date']}")
        
        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            smtp.send_message(msg)
            print(f"\n✓ Email sent to {smtp_host}:{smtp_port}")
            print(f"Check the phishing detector terminal for results.\n")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

def interactive_mode():
    
    print("\n" + "="*70)
    print("GMAIL TO LOCALHOST FORWARDER")
    print("="*70)
    print("\nChoose a method to forward Gmail emails to your phishing detector:\n")
    print("1. Fetch from Gmail via IMAP (automatic)")
    print("2. Paste raw email content (manual)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        print("\n" + "="*70)
        print("GMAIL IMAP SETUP")
        print("="*70)
        print("\nIMPORTANT: Use an App Password, not your regular Gmail password!")
        print("Create one at: https://myaccount.google.com/apppasswords\n")
        
        gmail_user = input("Gmail address: ").strip()
        gmail_password = getpass.getpass("App password: ")
        
        print("\nSearch options:")
        print("  ALL - All emails (latest 5)")
        print("  UNSEEN - Only unread emails")
        print("  SUBJECT 'keyword' - Emails with keyword in subject")
        
        search = input("\nSearch criteria (default: ALL): ").strip() or 'ALL'
        limit = input("Max emails to fetch (default: 5): ").strip() or '5'
        
        fetch_and_forward_gmail(
            gmail_user, 
            gmail_password,
            search_criteria=search,
            limit=int(limit)
        )
        
    elif choice == '2':
        print("\n" + "="*70)
        print("MANUAL EMAIL PASTE")
        print("="*70)
        print("\nSteps to get raw email from Gmail:")
        print("1. Open the email in Gmail")
        print("2. Click the three dots (⋮) → Show original")
        print("3. Click 'Copy to clipboard' or select all and copy")
        print("4. Paste below and press Enter, then Ctrl+D (or Ctrl+Z on Windows)\n")
        
        print("Paste raw email content below:")
        print("-" * 70)
        
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        raw_email = '\n'.join(lines)
        
        if raw_email.strip():
            send_raw_email_to_localhost(raw_email)
        else:
            print("\n✗ No content provided")
    
    elif choice == '3':
        print("\nExiting...")
        return
    else:
        print("\n✗ Invalid choice")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Forward Gmail emails to localhost phishing detector',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gmail_forwarder.py
  
  python gmail_forwarder.py --gmail user@gmail.com --fetch
  
  python gmail_forwarder.py --gmail user@gmail.com --fetch --search UNSEEN
  
  python gmail_forwarder.py --gmail user@gmail.com --fetch --search 'SUBJECT "phishing"'

IMPORTANT: You need a Gmail App Password (not your regular password)
Create one at: https://myaccount.google.com/apppasswords

"""
)

    parser.add_argument('--gmail', metavar='EMAIL', help='Gmail address to fetch from')
    parser.add_argument('--fetch', action='store_true', help='Fetch emails via IMAP')
    parser.add_argument('--search', default='ALL', metavar='CRITERIA',
                        help='IMAP search criteria (default: ALL)')
    parser.add_argument('--limit', type=int, default=5, metavar='N',
                        help='Max emails to fetch (default: 5)')
    parser.add_argument('--smtp-host', default='localhost', metavar='HOST',
                        help='Destination SMTP host (default: localhost)')
    parser.add_argument('--smtp-port', type=int, default=1025, metavar='PORT',
                        help='Destination SMTP port (default: 1025)')

    args = parser.parse_args()

    if args.gmail and args.fetch:
        import getpass
        password = getpass.getpass(f"App password for {args.gmail}: ")
        fetch_and_forward_gmail(
            gmail_user=args.gmail,
            gmail_password=password,
            smtp_host=args.smtp_host,
            smtp_port=args.smtp_port,
            limit=args.limit,
            search_criteria=args.search,
        )
    else:
        interactive_mode()

if __name__ == '__main__':
    main()
