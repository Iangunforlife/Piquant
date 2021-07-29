class ReferalCode:
    def __init__(self, codenum, status):
        self.__codenum = codenum
        self.__status = status

    def get_codenum(self):
        return self.__codenum

    def get_status(self):
        return self.__status

    def set_status(self, status):
        self.__status = status
