class Item:
    def __init__(self, id, w, h, d):
        self.id = id
        # Use only unique orientations
        self.orientations = list(set([(w, h, d), (w, d, h), (h, w, d),
                                      (h, d, w), (d, w, h), (d, h, w)]))
        self.volume = w * h * d  # Pre-calculate volume for sorting
