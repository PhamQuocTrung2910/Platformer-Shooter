import pygame

#button class
# A clickable image used for Start, Exit and Restart.
class Button():
	def __init__(self,x, y, image, scale):
		# Resize the image by the given scale factor
		width = image.get_width()
		height = image.get_height()
		self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
		# The rect is the button's position/size, used to detect mouse hovering
		self.rect = self.image.get_rect()
		self.rect.topleft = (x, y)
		# Remembers if the mouse button is already held down (prevents repeat clicks)
		self.clicked = False

	def draw(self, surface):
		# Returns True only on the frame the button is clicked
		action = False

		#get mouse position
		pos = pygame.mouse.get_pos()

		#check mouseover and clicked conditions
		if self.rect.collidepoint(pos):
			# Left button down AND we haven't already counted this click
			if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
				action = True
				self.clicked = True

		# Once the mouse is released, allow a new click
		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False

		#draw button
		surface.blit(self.image, (self.rect.x, self.rect.y))

		return action