"""
邮件服务
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务"""

    @staticmethod
    def send_verification_code(email: str, code: str) -> bool:
        """
        发送验证码邮件

        Args:
            email: 收件人邮箱
            code: 验证码

        Returns:
            是否发送成功
        """
        if not settings.smtp_username or not settings.smtp_password:
            logger.warning("SMTP配置未完成，验证码发送已禁用")
            logger.info(f"[开发模式] 验证码: {code}")
            return True

        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header('账户注册验证码', 'utf-8')
            msg['From'] = f"{settings.email_from_name} <{settings.smtp_username}>"
            msg['To'] = email

            # HTML邮件内容
            html_content = f"""
            <html>
                <body>
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                            账户注册验证
                        </h2>
                        <p style="color: #666; font-size: 14px; margin: 20px 0;">
                            您正在注册容诚税务师事务所智能化平台账户。
                        </p>
                        <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                            <p style="color: #999; font-size: 12px; margin: 0 0 10px 0;">验证码</p>
                            <p style="font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 5px; margin: 0;">
                                {code}
                            </p>
                        </div>
                        <p style="color: #999; font-size: 12px; margin: 20px 0;">
                            此验证码有效期为5分钟。请不要将验证码分享给任何人。
                        </p>
                        <p style="color: #999; font-size: 12px; margin: 20px 0;">
                            如果您没有进行此操作，请忽略此邮件。
                        </p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                        <p style="color: #999; font-size: 11px; margin: 0;">
                            © 2024 容诚税务师事务所。版权所有。
                        </p>
                    </div>
                </body>
            </html>
            """

            # 添加HTML内容
            part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part)

            # 发送邮件
            # 根据端口选择SSL或STARTTLS连接方式
            if settings.smtp_port == 465:
                # 使用SSL加密连接（端口465）
                with smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port) as server:
                    server.login(settings.smtp_username, settings.smtp_password)
                    server.send_message(msg)
            else:
                # 使用STARTTLS加密连接（端口587或25）
                with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                    server.starttls()
                    server.login(settings.smtp_username, settings.smtp_password)
                    server.send_message(msg)

            logger.info(f"验证码邮件已发送至: {email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(f"SMTP认证失败: 用户名或密码不正确")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"邮件发送出错: {str(e)}")
            return False

    @staticmethod
    def send_reset_password_code(email: str, code: str) -> bool:
        """
        发送密码重置验证码邮件

        Args:
            email: 收件人邮箱
            code: 验证码

        Returns:
            是否发送成功
        """
        if not settings.smtp_username or not settings.smtp_password:
            logger.warning("SMTP配置未完成，验证码发送已禁用")
            logger.info(f"[开发模式] 密码重置验证码: {code}")
            return True

        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header('密码重置验证码', 'utf-8')
            msg['From'] = f"{settings.email_from_name} <{settings.smtp_username}>"
            msg['To'] = email

            # HTML邮件内容
            html_content = f"""
            <html>
                <body>
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                            密码重置验证
                        </h2>
                        <p style="color: #666; font-size: 14px; margin: 20px 0;">
                            您正在重置容诚税务师事务所智能化平台账户密码。
                        </p>
                        <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                            <p style="color: #999; font-size: 12px; margin: 0 0 10px 0;">验证码</p>
                            <p style="font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 5px; margin: 0;">
                                {code}
                            </p>
                        </div>
                        <p style="color: #999; font-size: 12px; margin: 20px 0;">
                            此验证码有效期为5分钟。请不要将验证码分享给任何人。
                        </p>
                        <p style="color: #999; font-size: 12px; margin: 20px 0;">
                            如果您没有进行此操作，请忽略此邮件并确保账户安全。
                        </p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                        <p style="color: #999; font-size: 11px; margin: 0;">
                            © 2024 容诚税务师事务所。版权所有。
                        </p>
                    </div>
                </body>
            </html>
            """

            # 添加HTML内容
            part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part)

            # 发送邮件
            # 根据端口选择SSL或STARTTLS连接方式
            if settings.smtp_port == 465:
                # 使用SSL加密连接（端口465）
                with smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port) as server:
                    server.login(settings.smtp_username, settings.smtp_password)
                    server.send_message(msg)
            else:
                # 使用STARTTLS加密连接（端口587或25）
                with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                    server.starttls()
                    server.login(settings.smtp_username, settings.smtp_password)
                    server.send_message(msg)

            logger.info(f"密码重置验证码邮件已发送至: {email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(f"SMTP认证失败: 用户名或密码不正确")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"邮件发送出错: {str(e)}")
            return False
