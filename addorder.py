class addorder:
    def __init__(self, tablenum):
        self.__tablenum = tablenum
        self.__order_summary = {"F01": 0, "F02": 0, "F03": 0, "F04": 0, "F05": 0, "F06": 0, "F07": 0, "F08": 0, "F09": 0, "F10": 0}

    def add_order(self, order):
        for a in self.__order_summary:
            if a == order:
                newcount = self.__order_summary.get(a) + 1
                self.__order_summary[a] = newcount

    def delete_order(self, deleteordercode):
        for a in self.__order_summary:
            if a == deleteordercode:
                self.__order_summary[a] = 0

    def update_order(self, deleteordercode):
        for a in self.__order_summary:
            if a == deleteordercode:
                newcount = self.__order_summary.get(a) - 1
                self.__order_summary[a] = newcount

    def get_tablenum(self):
        return self.__tablenum

    def get_order(self):
        return self.__order_summary

    def get_price(self):
        total = 0
        for a in self.__order_summary:
            total = total + (self.getpricefromcode(a) * self.__order_summary[a])
        return total


    def getnamefromcode(self, code):
        if code == 'F01':
            return "Foie Gras"
        elif code == "F02":
            return "Mushroom Soup"
        elif code == "F03":
            return "150g Wagyu Beef"
        elif code == "F04":
            return "Lobster Risotto"
        elif code == "F05":
            return "Chocolate Fondle"
        elif code == "F06":
            return "Eclair"
        elif code == "F07":
            return "Espresso"
        elif code == "F08":
            return "Singapore Mocktail"
        elif code == "F09":
            return "1992 Wines"
        elif code == "F10":
            return "Champagne"


    def getpricefromcode(self, code):
        if code == 'F01':
            return 12
        elif code == "F02":
            return 6
        elif code == "F03":
            return 75
        elif code == "F04":
            return 40
        elif code == "F05":
            return 20
        elif code == "F06":
            return 15
        elif code == "F07":
            return 10
        elif code == "F08":
            return 13
        elif code == "F09":
            return 70
        elif code == "F10":
            return 90


