import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from decouple import config

def generate_and_send_otp(to_email, length=4):
    # Function to generate OTP
    def generate_otp(length):
        otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
        return otp

    # Function to send email
    def send_email(to_email, otp):
        from_email = config('EMAIL_HOST_USER')
        from_password = config('EMAIL_HOST_PASSWORD')  # Use an app-specific password
     


        # Create the email content
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = "Your OTP Code"

        body = f"Your OTP code is {otp}"
        msg.attach(MIMEText(body, 'plain'))

        # Connect to the server and send the email
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(from_email, from_password)
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            print(f"Email sent successfully to {to_email}")
        except Exception as e:
            print(f"Failed to send email: {str(e)}")

    # Generate OTP
    otp = generate_otp(length)
    print(f"Generated OTP: {otp}")

    # Send the OTP via email
    send_email(to_email, otp)
    return otp
