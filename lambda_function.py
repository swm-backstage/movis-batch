import os
import json
import mysql.connector
from sdk.api.message import Message
from sdk.exceptions import CoolsmsException

def lambda_handler(event, context):
    db = mysql.connector.connect(
        host=os.environ['DB_HOST'],
        port=int(os.environ['DB_PORT']),
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        db=os.environ['DB_NAME'],
        # auth_plugin='mysql_native_password'
    )
    cursor = db.cursor(dictionary=True)
    
    # TODO : 메시지 보낼 인원의 기간 처리
    query = """
    SELECT
        em.member_id,
        em.event_id,
        m.phone_no,
        e.name AS event_name,
        e.total_payment_amount,
        e.payment_deadline,
        e.club_id,
        c.name AS club_name
    FROM event_member em
    JOIN member m ON em.member_id = m.ulid
    JOIN event e ON em.event_id = e.ulid
    JOIN club c ON e.club_id = c.ulid
    WHERE em.is_paid = FALSE
    """
    cursor.execute(query)
    unpaid_members = cursor.fetchall()
    
    # CoolSMS 설정
    api_key = os.environ['COOLSMS_API_KEY']
    api_secret = os.environ['COOLSMS_API_SECRET']
    

    cool = Message(api_key, api_secret)
    # 메시지 전송
    # TODO : 한 유저가 여러 메시지를 받아야 하는 경우에 대한 처리
    # TODO : 아이폰 기준 제목이 나타나지 않는 오류
    for member in unpaid_members:
        message = (
            f"[모비스 - 모임을 위한 비서 서비스]\n"
            f"⌜{member['club_name']}⌟의 미납된 회비가 존재합니다.\n"
            f"- 이벤트명 : {member['event_name']}\n"
            f"- 납부 액 : {member['total_payment_amount']}\n"
            f"- 납부 기한 : {member['payment_deadline']}"
        )
        
        params = {
            'type': 'LMS',
            'to': member['phone_no'],
            'from': os.environ['SENDER_NUMBER'],
            'text': message.strip(),
            'autoTypeDetect': 'false'
        }
    
        try:
            response = cool.send(params)
            print("메시지 전송 성공:", response)
        except CoolsmsException as e:
            print("메시지 전송 실패 - 에러코드: ", e.code)
            print("메시지 전송 실패 - 에러메시지:", e.msg)
    
    cursor.close()
    db.close()
    
    return {
        'statusCode': 200,
        'body': json.dumps('메시지가 성공적으로 전송되었습니다.')
    }