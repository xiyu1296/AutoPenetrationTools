from passlib.context import CryptContext






# 密码加密配置
PwdContext = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)



class PwdUtil:

    # 密码验证
    @classmethod
    def verify_password(cls,password:str, hashed_password: str):

        return PwdContext.verify(password,hashed_password)


    # 密码加密
    @classmethod
    def set_password_hash(cls, password: str):

        return PwdContext.hash(password)