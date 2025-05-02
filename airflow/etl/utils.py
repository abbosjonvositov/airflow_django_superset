class XComDataWrapper:
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return f"XComDataWrapper({len(self.data)} records stored)"