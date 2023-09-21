from app import db

class Video(db.Model):
    # 테이블 이름 설정
    __tablename__ = 'videos'

    id = db.Column(db.Integer, primary_key=True)
    video_name = db.Column(db.String(200), nullable=False)
    video_file = db.Column(db.LargeBinary, nullable=False)
    upload_date = db.Column(db.DateTime(), nullable=False)