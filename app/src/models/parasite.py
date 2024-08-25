class Correct:
    def __init__(self, word: str, incorrectUsage: str, correctUsage: str):
        self.word = word
        self.incorrectUsage = incorrectUsage
        self.correctUsage = correctUsage

class Parasite:
    def __init__(self, word: str, correctVersions: Correct, filename: str, id: int):
        self.word = word
        self.correctVersions = correctVersions
        self.filename = filename
        self.id = id

# c1 = Correct("word", "inc", "cor")
# p1 = Parasite("wordKAZ", c1, "fielanme", 0)
# print(p1)