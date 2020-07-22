import os
base_dir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'noobshehe'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(base_dir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['admin@invite.com']
    POSTS_PER_PAGE = 25
    VAPID_PRIVATE_KEY = "SOz4qDUZaEUp1PapnoK-PMSGK5zr_rfzjuFH8JLijLk"
    VAPID_PUBLIC_KEY = "BIcdW51BZR5cUZNiQaRSch7HN87COzub8QebqeQ5j5oukcGQvG86FJI14Nq9L04UU4B7pbm1skhwAYr0Surk2Ng"
    VAPID_CLAIMS = {"sub": "mailto:test@test.in"}