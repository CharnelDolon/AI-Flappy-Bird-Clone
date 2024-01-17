import pygame
import neat 
import time 
import os 
import random 
pygame.font.init()

WIN_WIDTH = 500
WIN_HEIGHT = 800

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 50)

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20 
    ANIMATION_TIME = 5 

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0 
        self.img = self.IMGS[0]

    def move(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def flap(self):
        self.tick_count += 1
        # Determines the bird's arc after flap | -10.5*1 + 1.5*1^2 = -9 
        d = self.vel*self.tick_count + 1.5*self.tick_count**2
        
        # Terminal velocity when d == 16.
        if d >= 16:
            d = 16
        if d < 0:
            d -= 2

        # Update bird.y
        self.y = self.y + d

        # Determines when bird should be tilted upright or downwards
        if d < 0 or self.y < self.height + 50:
            # Prevent tilt past MAX_ROTATION
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            # Nosedive
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        # Method that handles bird animation and rotation
        self.img_count += 1

        # Determine bird.png flap animation 
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # Stop flap animation if bird is nosediving
        if self.tilt <= -80: 
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2
        
        # Code taken from stack overflow that rotates bird image according to tilt around its center axis
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)
        
    def get_mask(self):
        # Collision handling
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    VEL = 1
    
    def __init__ (self, x):
        self.x = x 
        self.height = 0 
        self.gap = 100 

        self.top = 0 
        self.bottom = 0 
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()
    
    def set_height(self):
        # Set a random height place two pipes with a gap in between
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP
    
    def move(self):
        self.x -= self.VEL
    
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        '''
        Masks determines the parts of the image where it is transparent or are pixels,
        Collisions can be handled by creating 2d lists with as much rows as pixels going down
        and as many columns as there is pixels going across. The seperate lists are compared and
        are what determine if any pixels collide with eachother, creating pixel perfect collision.
        '''
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # Determine offset that checks pixels how pixels are 
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # Find point of collision
        bottom_point = bird_mask.overlap(bottom_mask, bottom_offset)
        top_point = bird_mask.overlap(top_mask, top_offset)

        # If t_point or b_point does not collide return
        if top_point or bottom_point:
            return True 
        return False

class Base:
    VEL = 1
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG 
    
    def __init__(self, y):
        self.y = y
        self.x1 = 0 
        self.x2 = self.WIDTH

    def move(self):
        '''
        Create 2 BASE_IMGs, one starting at position 0 and the other after the width of the 
        first image. Both images move together and loop creating the illusion of moving ground
        '''
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # Replace the image outside the window behind the next image
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0: 
            self.x2 = self.x1 + self.WIDTH 
    
    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

def draw_window(win, bird, pipes, base, score):
    # Blit == Draw
    win.blit(BG_IMG, (0,0))
    for pipe in pipes:
        pipe.draw(win)
    
    text = STAT_FONT.render("Score: " + str(score), 1,(255,255,255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    base.draw(win)
    bird.draw(win)
    pygame.display.update()

def main(genomes, config):
    '''
    Initialize 3 lists, to keep track of the bird that the nueral network is controlling 
    i.e. the position and genome to be able to change fitness values.
    '''
    nets = []
    ge = []
    birds = []

    # Setup a neural network for the genomes and tracks invidual birds
    for g in genomes:
        # Net evaluates the genome and config file
        net = neat.nn.FeedForwardNetwork(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0 
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    score = 0

    run = True 
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: run = False0
            
        # Check for which pipe the activation function takes account of
        pip_ind = 0
        if len(birds) > 0:
            # If first bird has passed the first pipe on the list: look for the next pipe
            if len(pipes) > 1 and bird[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1
            

        add_pipe = False
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                # If bird collides with pipe object: decrease fitness and remove bird object
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)
            
                # If pipe is passed generate a new pipe object
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True 
                    add_pipe = True
            
            # If pipe exits window remove existing pipe object
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            
            pipe.move()
        
        # Increment score and generate new pipe object
        if add_pipe:
            score += 1
            # Each time a bird object passes a pipe increase its fitness
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))
        
        for r in rem: 
            pipes.remove(r)
        
        for x, bird in enumerate(birds):
        # If bird hits base object: remove bird object
            if bird.y + bird.img.get_height() >= 730:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win, bird, pipes, base, score)
    
    pygame.quit()
    quit()

main()

def run(config_path):
    # Define all subheadings and it's properties from the text file 
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, 
                                config_path)
    p = neat.Population(config)
    # Print detailed stats such as the fitness of each genaration in the console.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Run main functions 50 times (50 generations)
    winner = p.run(main,50)

if __name__ == "__main__":
    # Give path to directory 
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)



