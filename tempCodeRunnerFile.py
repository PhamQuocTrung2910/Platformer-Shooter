    else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False