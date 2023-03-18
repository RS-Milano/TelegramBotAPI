from json import loads
from time import asctime
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import HTTPError

class TelegramBot():
    """Basic class that contains the main logic and methods of the bot"""

    def __init__(self, TOKEN: str, TIMEOUT: int = 3600, ADMINCHATID: int = 0, LOGFILEPATH: str = 0) -> None:
        """Mandatory argument:
        TOKEN - your telegram API token
        Optionals arguments:
        TIMEOUT - time in seconds after which the bot will update the request
        when waiting longtime polling (better if more than 60)
        ADMINCHATID - if specified, the bot will send error messages
        LOGFILEPATH - if specified, the bot will write errors to logfile"""

        self.URL: str = "https://api.telegram.org/bot" + TOKEN + "/"
        self.TIMEOUT: int = TIMEOUT
        self.ADMINCHATID: int = ADMINCHATID
        self.LOGFILEPATH: str = LOGFILEPATH
        self.offset: int = 0

    def sendRequest(self, method: str, data: list[tuple]) -> dict:
        """Sends a url request to telegram bot API, and if successful,
        returns the contents of the dict-transformed response.
        If an error occurs, handles the error if specified"""

        data = bytes(urlencode(data), encoding = "UTF-8")
        newRequest = Request(self.URL + method, data)
        try:
            with urlopen(newRequest) as connection:
                response: dict = loads(connection.read().decode("utf-8").replace("\n", ""))
        except Exception as error:
            self.errorHandler(error)
        else:
            if not response["ok"]:
                if self.ADMINCHATID:
                    self.sendMsgToAdmin(response)
                if self.LOGFILEPATH:
                    self.writeLog(response)
            else:
                return response["result"]

    def getUpdate(self) -> dict:
        """Receives incoming updates one at a time"""

        data = [("offset", self.offset), ("limit", 1), ("timeout", self.TIMEOUT)]
        response = self.sendRequest("getUpdates", data)
        if response:
            self.offset = response[0]["update_id"] + 1
        return response

    def sendMsg(self, chatID: int, text: str) -> dict:
        """Sends text message to telegram user with chatID"""

        data = [("chat_id", chatID), ("text", text)]
        return self.sendRequest("sendMessage", data)

    def sendMsgToAdmin(self, msg: str) -> dict:
        """If self.ADMINCHATID is specified sends messages with errors to the admin on telegram"""

        return self.sendMsg(self.ADMINCHATID, msg)

    def sendKeyboard(self, chatID: int, text: str, keyboard) -> dict:
        """Sends message with Keyboard (ReplyKeyboard or InlineKeyboard) to telegram user with chatID"""

        data = [("chat_id", chatID), ("text", text), ("reply_markup", keyboard)]
        return self.sendRequest("sendMessage", data)

    def deletMessage(self, chatID: int, message_id: int) -> dict:
        """Deletes the message with message_id from chat with chatID"""

        data = [("chat_id", chatID), ("message_id", message_id)]
        return self.sendRequest("deleteMessage", data)

    def writeLog(self, msg: str) -> None:
        """If self.LOGFILEPATHA is specified write errors to log with timestamp"""

        with open(self.LOGFILEPATH, "a", encoding = "utf-8") as file:
            file.writelines("-" * 10 + "\n" + asctime() + "\n" + msg + "\n")

    def errorHandler(self, error: Exception) -> None:
        """Handles errors when sends url requests. If self.ADMINCHATID is specified,
        sends messages with errors to the admin on telegram. If self.LOGFILEPATH
        is spesified write errors to log"""

        if type(error) == HTTPError:
            msg = error.filename + "\n" + error.read().decode("utf-8")
            if self.ADMINCHATID:
                self.sendMsgToAdmin(msg)
            if self.LOGFILEPATH:
                self.writeLog(msg)
        else:
            tb = error.__traceback__.tb_frame.f_locals
            tb.pop("chatID", None)
            tb.pop("text", None)
            tb.pop("keyboard", None)
            tb.pop("url", None)
            msg = str(error) + "\n" + str(error.__traceback__.tb_frame) + "\n" + str(tb)
            if self.ADMINCHATID:
                self.sendMsgToAdmin(msg)
            if self.LOGFILEPATH:
                self.writeLog(msg)

class InlineKeyboard():
    """Class implements InlineKeyboardMarkup type from Telegram Bot API.
    Implements only two fields "text" and "callback_data" which have the same data.
    On initialisation, it takes an argument of type list, consisting of rows (also of type list)
    of buttons (type str - name of the button). For example:
    InlineKeyboard([["First button of the first row", "Second button of the first row"],[""First button of the second row"]])"""

    def __init__(self, inlineButtons: list[list[str]]) -> None:
        self.inlineButtons = inlineButtons

    def __str__(self) -> str:
        """The method returns a text representation of the InlineKeyboard to be used as the request url parameter"""

        result = '{"inline_keyboard":['
        for row in self.inlineButtons:
            result += '['
            for button in row:
                text = button
                result += '{"text":"' + text + '","callback_data":"' + text + '"}'
            result += '],'
        result = result[:-1] + ']}'
        return result

class ReplyKeyboard():
    """Class implements ReplyKeyboardMarkup type from Telegram Bot API. Optionals fields "resize_keyboard"
    and "one_time_keyboard" set to true. On initialisation, it takes an argument of type list, consisting
    of rows (also of type list) of buttons (type str - name of the button). For example:
    ReplyKeyboard([["First button of the first row", "Second button of the first row"],[""First button of the second row"]])"""

    def __init__(self, keyboardButtons: list[list[str]]) -> None:
        self.keyboardButtons = keyboardButtons

    def __str__(self) -> str:
        """The method returns a text representation of the ReplyKeyboard to be used as the request url parameter"""

        result = '{"keyboard":['
        for row in self.keyboardButtons:
            result += '['
            for button in row:
                result += '"' + button + '"'
            result += '],'
        result = result[:-1] + ']'
        result += ',"resize_keyboard":true,"one_time_keyboard":true}'
        return result
