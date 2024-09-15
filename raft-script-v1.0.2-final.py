import pygame as pg
from sys import exit
import numpy as np

##################################################################################
# NOTA DE ATUALIZAÇÃO (V1.0.2)
# provável versão final do projeto
# finalizada em 27/11/2022

# NOVA MECÂNICA DE PESCA (DISTANTE E NORMAL)
# TUTORIAL ADICIONADO
# NUMPY IMPLEMENTADO
# RANDOM AGORA GERADO PELO NUMPY
# COMENTÁRIOS NAS FUNÇÕES
# TODA A SEÇÃO DE MOBILE REMOVIDA

##################################################################################

# setup inicial
pg.init()
screen = pg.display.set_mode((700, 700))
rng = np.random.default_rng()
pg.display.set_caption("RAFT")
pg.display.set_icon(pg.image.load('Assets/raft_icon.png').convert_alpha())
clock = pg.time.Clock()

# VARIÁVEIS --------------------------------------------
tile = 140
centro_da_tela = (350, 350)
frame_atual = 0
oceano_pos = -144
delay_pesca = 400
intro = True
end = False
debug = 0

# quantias
qnt_dias = 0
qnt_peixe = 0
qnt_madeira = 999

# lista de inputs
setas = [pg.K_DOWN, pg.K_UP, pg.K_LEFT, pg.K_RIGHT]
direcoes = ["baixo","cima","esquerda","direita"]
wasd = [pg.K_s, pg.K_w, pg.K_a, pg.K_d]

# MATRIZ MAPA
pos_jogador = [2,2]
mapa = np.array([
    [0,0,0,0,0], # 0 significa nada (mar)
    [0,1,1,1,0], # 1 significa lugar onde madeiras podem spawnar
    [0,1,2,1,0], # 2 significa lugares onde há jangada
    [0,1,1,1,0],
    [0,0,0,0,0]
])

# CLASSES ----------------------------------------------

# JOGADOR
class Naufrago(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pg.transform.scale(pg.image.load('Assets/Naufrago/naufrago_Default.png').convert_alpha(), (432, 432))
        self.rect = self.image.get_rect(center=centro_da_tela)

        # variações
        self.image_b = pg.transform.scale(pg.image.load('Assets/Naufrago/naufrago_Back.png').convert_alpha(), (432, 432))
        self.image_l = pg.transform.scale(pg.image.load('Assets/Naufrago/naufrago_Left.png').convert_alpha(), (432, 432))
        self.image_r = pg.transform.scale(pg.image.load('Assets/Naufrago/naufrago_Right.png').convert_alpha(), (432, 432))

        # sprites
        self.sprites = [self.image,self.image_b,self.image_l,self.image_r]
        self.sprite_state = 0

    def update_sprite(self):
        self.image = self.sprites[self.sprite_state]

# visão do jogador
class NaufragoVision(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pg.image.load('Assets/Naufrago/naufrago_vision.png').convert_alpha()
        self.rect = self.image.get_rect(center=(2.5*tile,3.5*tile))

        # variações
        self.ativado = self.image
        self.desativado = pg.image.load('Assets/Naufrago/naufrago_vision_desativada.png').convert_alpha()
        self.state = True

        self.distancia = 'curta'
        
        # posições
        self.pos = [
            (350, 3.5*tile),
            (350, 1.5*tile),
            (1.5*tile, 350),
            (3.5*tile, 350)]

    def checar_pescabilidade(self):
        if pg.sprite.spritecollide(naufrago_vision,tiles_impescaveis,False):
            self.image = self.desativado
            self.state = False
        else:
            self.image = self.ativado
            self.state = True

    def alterar_distancia(self):
        if self.distancia == 'curta':
            self.pos = [
                (350,4.5*tile),
                (350,0.5*tile),
                (0.5*tile,350),
                (4.5*tile,350)]
            self.distancia = 'longa'
        else:
            self.pos = [
                (350, 3.5*tile),
                (350, 1.5*tile),
                (1.5*tile, 350),
                (3.5*tile, 350)]
            self.distancia = 'curta'
            
# rect que torna um lugar impescável
class TileImpescavel(pg.sprite.Sprite):
    def __init__(self, pos, player_pos):
        super().__init__()
        self.image = pg.Surface((100,100))
        self.image.fill('Red')
        self.rect = self.image.get_rect(center=pos)
        self.pos = list(self.rect.center)
        self.pos_inic_jog = player_pos
        self.tempo = 0

    def update(self,player_pos,direcao='nenhuma'):
        if direcao == "cima":
            self.pos_inic_jog = [self.pos_inic_jog[0],self.pos_inic_jog[1]+1]           # a direção é usada quando expandir a mapa para corrigir
        elif direcao == "esquerda":                                                     # a posição dos impescáveis em relação à do jogador
            self.pos_inic_jog = [self.pos_inic_jog[0]+1,self.pos_inic_jog[1]]           # (só acontece em dois casos específicos)
        else:
            nova_pos_jog = player_pos
            self.rect.centerx = self.pos[0] + 140 * (self.pos_inic_jog[0]-nova_pos_jog[0])  # corrige a posição das áreas quando o jogador anda
            self.rect.centery = self.pos[1] + 140 * (self.pos_inic_jog[1]-nova_pos_jog[1])  # para que elas estejam sempre no lugar específico
            
        if self.tempo == frame_atual:
            self.kill()

# OBJETOS E CENÁRIO

# jangada
class Jangada(pg.sprite.Sprite):
    def __init__(self,posicao):
        super().__init__()
        self.image = pg.transform.scale(pg.image.load('Assets/jangada.png').convert_alpha(), (144, 144))
        self.rect = self.image.get_rect(topleft=tuple(posicao))
        self.pos = jangada_posicoes(matriz_visivel(mapa,pos_jogador))
    
    def update(self):
        self.pos = jangada_posicoes(matriz_visivel(mapa,pos_jogador))
        jangada_group.empty()
        for i in self.pos:
            jangada_group.add(Jangada(i))

# madeira
class Madeira(pg.sprite.Sprite):
    def __init__(self,matriz,tempo,player_pos_inic):
        super().__init__()
        self.image = pg.transform.scale(pg.image.load('Assets/Madeira/madeira_boiando.png').convert_alpha(),(72,72))
        self.rect = self.image.get_rect()
        self.pos = rng.choice(madeira_posicoes(matriz))
        self.pos_inic_jog = player_pos_inic
        self.rect.center = self.pos
        self.surgimento = tempo
        self.tempo = rng.integers(3*fps, 5*fps)
        
            
    def update(self,player_pos,direcao='nenhuma'):
        if direcao == "cima":
            self.pos_inic_jog = [self.pos_inic_jog[0],self.pos_inic_jog[1]+1]
        elif direcao == "esquerda":
            self.pos_inic_jog = [self.pos_inic_jog[0]+1,self.pos_inic_jog[1]]
        else:
            nova_pos_jog = player_pos
            self.rect.centerx = self.pos[0] + tile * (self.pos_inic_jog[0]-nova_pos_jog[0])
            self.rect.centery = self.pos[1] + tile * (self.pos_inic_jog[1]-nova_pos_jog[1])

            if frame_atual > self.tempo + self.surgimento:
                self.kill()
            
# classe da barra de fome
class Fome():
    def __init__(self):
        # counter de eventos
        self.counter = 0
        
        # importando sprites
        self.sprites = []
        
        for i in range(0,9):
            imagem = pg.image.load(f'Assets/Fome/fome{i}.png').convert_alpha()
            self.sprites.append(pg.transform.scale(imagem ,(144,144)))

        self.image = self.sprites[0]

    def update_sprite(self):
        self.counter += 1
        if self.counter == 9:
            self.counter = 1
        
        if self.sprites.index(self.image) < 7:
            self.image = self.sprites[self.sprites.index(self.image)+1]
        else:
            self.image = self.sprites[0]

# classe do sol-relogio
class Sol():
    def __init__(self):
        # importando sprites
        self.sprites = []
        
        for i in range(0,9):
            imagem = pg.image.load(f'Assets/Sol/sol_{i}.png').convert_alpha()
            self.sprites.append(pg.transform.scale2x(imagem))

        self.image = self.sprites[0]

    def update_sprite(self):
        if self.sprites.index(self.image) < 7:
            self.image = self.sprites[self.sprites.index(self.image)+1]
        else:
            self.image = self.sprites[0]
        

# FUNÇÕES -----------------------------------------------

def pesca_peixe(quant_peixe):                                                   # como o nome sugere, a função serve para pescar os peixes
    quant_peixe += 1                                                            # alterando o valor em +1, além disso, cria um tile impescável
    som_pesca.play()                                                            # naquela região que será detectado pela visão[+] quando preciso.
    impescavel = TileImpescavel(naufrago_vision.rect.center,pos_jogador)
    tiles_impescaveis.add(impescavel)
    impescavel.tempo = frame_atual + delay_pesca
    return quant_peixe

def pesca_madeira(quant_madeira):                                               # tem a mesma função da anterior, a diferença
    quant_madeira += 1                                                          # é que o valor alterado aqui é o de madeiras.
    som_pesca_madeira.play()
    impescavel = TileImpescavel(naufrago_vision.rect.center,pos_jogador)
    tiles_impescaveis.add(impescavel)
    impescavel.tempo = frame_atual + delay_pesca
    return quant_madeira


def resetar_valores(matriz, player_pos, quant_madeira):
    matriz  = np.array([
        [0,0,0,0,0],
        [0,1,1,1,0],                                        # usada no fim de jogo para resetar a mapa e a pos do jogador
        [0,1,2,1,0],                                        # também zera a quantidade de madeiras
        [0,1,1,1,0],
        [0,0,0,0,0]
    ])
    player_pos = [2,2]
    quant_madeira = 5
    
    return matriz, player_pos, quant_madeira


def matriz_visivel(matriz, player_pos):       #          recebe matrizes gigantes e
                                              #  retorna um recorte 5x5 com centro na player_pos
    nova_matriz = matriz[
        player_pos[1]-2:player_pos[1]+3,      # essa função é importante para que só seja renderizado
        player_pos[0]-2:player_pos[0]+3]      #    o que é visível para o jogador no momento

    return nova_matriz


def expandir_matriz(player_pos,direcao,matriz):
    dimensoes_x,dimensoes_y = matriz.shape                                  #     recebe uma matriz, uma direção e uma posição e
                                                                            #    retorna uma matriz maior na direção especificada
    # elemento a ser inserido                                               #   além de criar um número 2 adjacente à posição dada.
    elemento = 2
    
    if direcao == "baixo":
        matriz[player_pos[1]+1,player_pos[0]] = elemento
        matriz = np.append(matriz,np.zeros((1,dimensoes_y)),axis=0)         # EX.:
                                                                            #      recebe                   devolve
    if direcao == "cima":                                                   #      0 0 0 0 0                0 0 0 0 0 0     acrescenta uma
        matriz[player_pos[1]-1,player_pos[0]] = elemento                    #      0 0 0 0 0                0 0 0 0 0 0 ___ linha de zeros
        matriz = np.append(np.zeros((1,dimensoes_y)),matriz,axis=0)         #      0 0 2 0 0                0 0 2 2 0 0     no final e um
                                                                            #      0 0 0 0 0                0 0 0 0 0 0     2 adjacente
        player_pos = [player_pos[0],player_pos[1]+1]                        #      0 0 0 0 0                0 0 0 0 0 0
        madeira_group.update(player_pos,direcao)                            #      
        tiles_impescaveis.update(player_pos,direcao)                        #      direção = direita        * a posição muda em alguns casos
                                                                            #      pos = [2,2]               (quando a direção é cima e esquerda)
    if direcao == "esquerda":
        matriz[player_pos[1],player_pos[0]-1] = elemento
        matriz = np.append(np.zeros((dimensoes_x,1)),matriz,axis=1)
            
        player_pos = [player_pos[0]+1, player_pos[1]]
        madeira_group.update(player_pos,direcao)
        tiles_impescaveis.update(player_pos,direcao)
        
    if direcao == "direita":
        matriz[player_pos[1],player_pos[0]+1] = elemento
        matriz = np.append(matriz,np.zeros((dimensoes_x,1)),axis=1)
    
    return player_pos, matriz


def lugares_spawnaveis(matriz):                               #                                   EX.:       1                1 1 1
    matriz_espelho = matriz.copy()                            #   gera o padrão diamante de 1's            1 1 1            1 1 1 1 1
                                                              #      em volta de números 2               1 1 2 1 1        1 1 2 2 2 1 1
    dimensoes_x,dimensoes_y = matriz.shape                    #         na matriz dada.                    1 1 1            1 1 1 1 1
                                                              #                                              1                1 1 1
    elementos = np.nditer(matriz,flags=['multi_index'])
    for elmnt in elementos:
        if elmnt == 2:
            pos = elementos.multi_index
            matriz_espelho[pos[0],pos[1]-2:pos[1]+3] = np.ones(5)
            matriz_espelho[pos[0]-1:pos[0]+2,pos[1]-1:pos[1]+2] = np.ones((3,3))
            matriz_espelho[pos[0]-2:pos[0]+3,pos[1]] = np.ones(5)

    matriz_espelho = np.maximum(matriz_espelho,matriz)

    return matriz_espelho


def jangada_posicoes(matriz):                               # recebe uma matriz 5x5 que tenha números 2
    posicoes = []                                           # e retorna posições em pixels baseado
    elementos = np.nditer(matriz,flags=['multi_index'])     # na posição dos números 2 na matriz
    for elmnt in elementos:
        if elmnt == 2:
            pos = elementos.multi_index
            posicoes.append([pos[1]*tile,pos[0]*tile])
    return posicoes


def madeira_posicoes(matriz):                      #       recebe uma matriz com 1's e retorna 
    player_pos = pos_jogador                       #  posições em pixels baseado na posição dos 1's
    dimensoes_x = len(matriz[0])                   #               dentro da matriz
    dimensoes_y = len(matriz)
                                                                        #  Ex. de uma lista de posições organizada linha abaixo de linha:
    posicoes = []                                                       #
    elementos = np.nditer(matriz,flags=['multi_index'])                 #                         [210, 70],  [350, 70],
    for elmnt in elementos:                                             #              [70, 210], [210, 210], [350, 210], [490, 210],
        if elmnt == 1:                                                  #  [-70, 350], [70, 350],                         [490, 350], [630, 350],
            pos = elementos.multi_index                                 #              [70, 490], [210, 490], [350, 490], [490, 490],
            desvio = [pos[1]-player_pos[0]+2,pos[0]-player_pos[1]+2]    #                         [210, 630], [350, 630]]      
            posicoes.append([desvio[0]*140+70,desvio[1]*140+70])
    return posicoes


def checar_tecla(tecla,player_pos,matriz,quant_madeira,quant_peixe):              # A função mais importante do jogo, ela chama todas as outras
                                                                                  # baseado nos imputs do jogador, nela são checados o movimento de 
                                                                                  # virar para um lado, andar e pescar.
    if event.key == setas[tecla] or event.key == wasd[tecla]: #1
                                                                                        # 1 - if principal. Nele é checado de fato se uma tecla foi
        if naufrago.sprite_state != tecla: #2                                           #     pressionada usando o laço de eventos.
            naufrago.sprite_state = tecla
            naufrago_vision.rect.center = naufrago_vision.pos[tecla]                    # 2 - ação de virar. Se a direção que o naufrago está for diferente
            naufrago_vision.checar_pescabilidade()                                      #     da que foi pressionada, virar o naufrago e a visão[+] e alterar.
                                                                                        #     o estado da visão para [x] caso seja impescável.
        elif pg.sprite.spritecollide(naufrago_vision,jangada_group,False): #3
            if naufrago_vision.distancia == 'curta':
                player_pos = [player_pos[0],player_pos[1]+1] if tecla == 0 else player_pos  # 3 - ação de andar. Se o naufrago já estiver na posição pressionada,
                player_pos = [player_pos[0],player_pos[1]-1] if tecla == 1 else player_pos  #     houver uma jangada à frente e a visão for curta 
                player_pos = [player_pos[0]-1,player_pos[1]] if tecla == 2 else player_pos  #     a posição do jogador muda na direção dada.
                player_pos = [player_pos[0]+1,player_pos[1]] if tecla == 3 else player_pos
                                                                                            # 4 - ação de pescar. Se a visão[+] estiver ativa, caso haja colisão
        elif naufrago_vision.state: #4                                                      #     com madeiras quando clicar, pescar madeira, caso contrário,
            if pg.sprite.spritecollide(naufrago_vision,madeira_group,True):                 #     pescar peixe.
                quant_madeira = pesca_madeira(quant_madeira)
            elif naufrago_vision.distancia == 'curta':
                quant_peixe = pesca_peixe(quant_peixe)

    return player_pos, matriz, quant_madeira, quant_peixe


def checar_espaco(state,player_pos,matriz,quant_madeira,quant_peixe):                                 # Uma das funções mais importantes junto à
                                                                                                      # checar tecla. Checa a tecla espaço e caso
    if quant_madeira >= 4 and not pg.sprite.spritecollide(naufrago_vision,jangada_group,False):       # o jogador tenha madeira suficiente,
        if naufrago_vision.distancia == 'curta':                                                      # a visão esteja curta e o jogador
            if pg.sprite.spritecollide(naufrago_vision,madeira_group,True): #1                        # não esteja de frente para uma jangada
                quant_madeira = pesca_madeira(quant_madeira)                                          # expande a matriz mapa e cria uma nova.
            player_pos, matriz = expandir_matriz(player_pos,direcoes[state],matriz)
            matriz = lugares_spawnaveis(matriz)                                                       # 1 - caso o jogador esteja de frente para uma madeira
            quant_madeira -= 4                                                                        #     a madeira será pescada.
            som_jangada.play()

    return player_pos, matriz, quant_madeira, quant_peixe


# GRUPOS DE SPRITES -------------------------------------

# player
naufrago_vision = NaufragoVision()
naufrago = Naufrago()

tiles_impescaveis = pg.sprite.Group()
player_group = pg.sprite.Group()
player_group.add(naufrago_vision, naufrago)

# jangada
jangada_inicial = Jangada([280,280])

jangada_group = pg.sprite.Group()
jangada_group.add(jangada_inicial)

# madeira
madeira_group = pg.sprite.Group()


# ELEMENTOS INDIVIDUAIS ---------------------------------

tutorial = pg.image.load('Assets/tuto.png').convert_alpha()
modo_normal = pg.image.load('Assets/Modos/modo_pesca_normal.png').convert_alpha()
modo_distante = pg.image.load('Assets/Modos/modo_pesca_distante.png').convert_alpha()
madeira_icon = pg.transform.scale2x(pg.image.load('Assets/Madeira/madeira_icon.png').convert_alpha())
peixe = pg.transform.scale2x(pg.image.load('Assets/peixe.png').convert_alpha())
oceano = pg.image.load('Assets/oceano.png').convert()
modo_pesca = [modo_normal,modo_distante]
fome = Fome()
sol = Sol()

# TEXTOS ------------------------------------------------
fonte = pg.font.Font('Assets/Fonte/VCR_OSD_MONO.ttf', 36)
fonte_menor = pg.font.Font('Assets/Fonte/VCR_OSD_MONO.ttf', 20)

# SONS -------------------------------------------------
pg.mixer.init()
som_start = pg.mixer.Sound('Assets/Música/start.wav')
som_death = pg.mixer.Sound('Assets/Música/death.wav')
som_pesca = pg.mixer.Sound('Assets/Música/pesca.wav')
som_pesca_madeira = pg.mixer.Sound('Assets/Música/pesca_madeira.wav')
som_jangada = pg.mixer.Sound('Assets/Música/jangada.wav')

# TIMERS ------------------------------------------------

# gatilho para spawnar madeira
madeira_trigger = False

# gatilho para atualizar o sprite do sol
sol_trigger = False

# gatilho para atualizar o sprite da fome
fome_trigger = False


# TELA INICIAL ========================================================================

logo = pg.image.load('Assets/Logo/raft_logo.png').convert()
logo_bg = pg.image.load('Assets/Logo/logo_bg.png').convert_alpha()
logo_bg_x = logo_bg_y = -388
pg.mixer.music.set_volume(0.10)
musica_tela_inicial = pg.mixer.music.load('Assets/Música/musica_tela_inicial.wav')
tempo_inicial = 0

def iniciar():
    pg.mixer.music.play(-1)
    saida = 255
    opacidade = 255
    opacidade_logo_trigger = False
    tutorial_skip = False
    
    while saida > 0:
        tempo_inicial = pg.time.get_ticks()
        
        for event in pg.event.get():      
            # checagem de saída
            if event.type == pg.QUIT:
                pg.quit()
                exit()

            # se qualquer tecla for pressionada
            if event.type == pg.KEYDOWN:
                opacidade_logo_trigger = True
                if opacidade == 0:
                    tutorial_skip = True
                pg.mixer.music.stop()
                som_start.play()

        if opacidade_logo_trigger:
            opacidade -= 5
            logo.set_alpha(opacidade)
        opacidade = 0 if opacidade < 0 else opacidade

        screen.blit(logo_bg,(logo_bg_x,logo_bg_y))
        screen.blit(logo,(0,0))
        
        if opacidade == 0:
            screen.blit(tutorial,(72,110))

        if opacidade == 0 and tutorial_skip:
            saida -= 5
            tutorial.set_alpha(saida)

        pg.display.update()
        clock.tick(40)

    return tempo_inicial

# =====================================================================================

if intro:
    tempo_inicial = iniciar()


# ENCERRAMENTO ========================================================================


quadrados_enc = pg.surface.Surface((140,140))
quadrado_opacidade = pg.surface.Surface((700,700))
quadrados_enc.fill('Black')
quadrado_opacidade.fill((54,54,54))
pos_quadrados_inic = [(0,0),(0,560),(560,0),(560,560)]

pos_quadrados_anim = [
    (0,140),(420,0),(140,560),(560,420),
    (0,280),(280,0),(280,560),(560,280),
    (0,420),(140,0),(420,560),(560,140),
    (140,140),(140,420),(420,140),(420,420),
    (280,140),(140,280),(420,280),(280,420)]

tempo_encerramento = 0
tempo_de_jogo = 0

def encerrar():
    fim = False
    saida = 255
    pos_quadrados = pos_quadrados_inic.copy()
    anim_state = 0
    pg.mixer.music.stop()
    som_death.play()


    while saida > 0:

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
                
            if event.type == pg.KEYDOWN:
                if anim_state > 14:
                    fim = True
                    pg.mixer.music.set_volume(0.7)
                    musica_fundo = pg.mixer.music.load('Assets/Música/fundo_sonoro.wav')
                    pg.mixer.music.play(-1)
        
        # screen.fill((54,54,54))
        
        # animação dos quadrados

        for posicoes in pos_quadrados:
            screen.blit(quadrados_enc,posicoes)
        if anim_state <= 4:
            pos_quadrados += pos_quadrados_anim[anim_state*4:anim_state*4+4]
        elif anim_state == 5:
            pos_quadrados.append((280,280))
        anim_state += 1

        # naufrago
        screen.blit(naufrago.image,naufrago.rect.topleft)
        
        # peixe
        qnt_peixes_texto = fonte.render(f'{qnt_peixe}', False, 'White')
        screen.blit(qnt_peixes_texto, (0.5*tile, 0.1*tile))
        screen.blit(peixe, (0, 0))

        # fome icon
        screen.blit(fome.sprites[8],(4*tile,0))

        # texto
        texto_gameover = fonte.render('GAME OVER',False,'White')
        texto_de_morte = fonte.render('VOCÊ MORREU DE FOME!',False,'White')
        score = str(qnt_dias)
        texto_score = fonte_menor.render(f'você sobreviveu {score} dias',False,'White')
        texto_reinicio = fonte_menor.render('pressione qualquer tecla para recomeçar',False,'White')

        if anim_state > 6:
            screen.blit(texto_gameover,(1.85*tile,1.5*tile))
            screen.blit(texto_de_morte,(tile,3*tile))
        if anim_state > 10:
            screen.blit(texto_score,(1.5*tile-6*(len(score)-1),3.3*tile))
        if anim_state > 14:
            screen.blit(texto_reinicio,(0.8*tile,4*tile))

        # saida com opacidade
        if fim:
            saida -= 5
            quadrado_opacidade.set_alpha(255-saida)
            screen.blit(quadrado_opacidade,(0,0))
        else:
            pg.time.wait(300)

        pg.display.update()
        clock.tick(40)


    return tempo_encerramento


# LAÇO PRINCIPAL DO JOGO ==============================================================

# iniciando música
pg.mixer.music.set_volume(0.7)
musica_fundo = pg.mixer.music.load('Assets/Música/fundo_sonoro.wav')
pg.mixer.music.play(-1)

while True:
    # algumas variáveis importantes relacionadas ao tempo
    frame_atual += 1
    fps = int(clock.get_fps())
    tempo = pg.time.get_ticks() - tempo_inicial - tempo_encerramento - 3000
    tempo_s = tempo // 1000
    qnt_dias = tempo_s // 60  #a cada 60 segundos se passa 1 dia
    qnt_dias = 0 if qnt_dias < 0 else qnt_dias

    # iniciando música

    # LAÇO DE EVENTOS -----------------------------------------------------------------
    for event in pg.event.get():
        
        # checagem de saída
        if event.type == pg.QUIT:
            pg.quit()
            exit()

        # checagem do teclado
        if event.type == pg.KEYDOWN:
            if tempo_s >= 0:
                for i in range(4):
                    pos_jogador, mapa, qnt_madeira, qnt_peixe = checar_tecla(i,pos_jogador,mapa,qnt_madeira,qnt_peixe)
                    
                if event.key == pg.K_SPACE:
                    pos_jogador, mapa, qnt_madeira, qnt_peixe = checar_espaco(naufrago.sprite_state,pos_jogador,mapa,qnt_madeira,qnt_peixe)

                if event.key == pg.K_RSHIFT or event.key == pg.K_LSHIFT:
                    naufrago_vision.alterar_distancia()
                    naufrago_vision.rect.center = naufrago_vision.pos[naufrago.sprite_state]

    # eventos a cada X segundos -------------------------------------------------------

    if tempo_s > 0:

        # madeira a cada 7 segundos
        if tempo_s % 7 == 0 and madeira_trigger:
            madeira_group.add(Madeira(mapa,frame_atual,pos_jogador))
            madeira_trigger = False
        if (tempo_s - 1) % 7 == 0:
            madeira_trigger = True

        # fome a cada 16 segundos (cada frame a 2s)
        if tempo_s % 2 == 0 and fome_trigger:
            fome.update_sprite()                # a cada 2 segundos, atualizar sprite da fome
            if fome.counter == 8:               # checar se tá no 8 sprite pra
                qnt_peixe -= 1                  # comer um peixe.
                if qnt_peixe < 0:               # se o peixe ficar -1
                    end = True                  # ativa o encerramento e coloca a variável pra 0
                    qnt_peixe = 0
            fome_trigger = False
        if (tempo_s - 1) % 2 == 0:              # no segundo seguinte, ativa o trigger de novo
            fome_trigger = True

        # sol a cada 60 segundos (cada frame a 7.5s)
        if int(tempo/100) % 75 == 0 and sol_trigger:
            sol.update_sprite()
            sol_trigger = False
        if (int(tempo/100)-10) % 75 == 0:
            sol_trigger = True

    # CHECAGEM DE FIM DE JOGO ---------------------------------------------------------

    if end:
        encerrar()
        tempo_inicial = 0
        naufrago_vision.pos = [(350, 3.5*tile),(350, 1.5*tile),(1.5*tile, 350),(3.5*tile, 350)]
        mapa,pos_jogador,qnt_madeira = resetar_valores(mapa,pos_jogador,qnt_madeira)            # resetando todos os valores
        naufrago_vision.rect.center = naufrago_vision.pos[0]                                    # para os valores iniciais
        tempo_encerramento = pg.time.get_ticks()                                                # logo após encerrar
        naufrago_vision.distancia = 'curta'
        logo_bg_x = logo_bg_y = -388
        sol.image = sol.sprites[0]
        naufrago.sprite_state = 0
        tiles_impescaveis.empty()
        madeira_group.empty()
        
        end = False
    
    # COLOCANDO ELEMENTOS PRINCIPAIS NA TELA ------------------------------------------
    
    # oceano
    screen.blit(oceano, (oceano_pos, oceano_pos))
    oceano_pos += 0.5
    if oceano_pos == 0:
        oceano_pos -= 144

    # jangada
    jangada_group.draw(screen)
    jangada_group.update()

    # madeira
    madeira_group.update(pos_jogador)
    madeira_group.draw(screen)

    # jogador
    naufrago.update_sprite()
    player_group.draw(screen)
    
    # áreas impescáveis temporariamente
    tiles_impescaveis.update(pos_jogador)
    naufrago_vision.checar_pescabilidade()
    # tiles_impescaveis.draw(screen)  # as areas impescáveis ficarão vermelhas (debug)


    # ELEMENTOS DA INTERFACE (HUD)-----------------------------------------------------

    # peixe icon
    screen.blit(peixe, (0, 0))

    # madeira icon
    screen.blit(madeira_icon,(0,0.5*tile))

    # sol icon
    if tempo_s % 60 == 0:
        screen.blit(sol.sprites[8],(4.5*tile,4.5*tile))
    else:
        screen.blit(sol.image,(4.5*tile,4.5*tile))

    # fome icon
    if tempo_s % 16 == 0:
        screen.blit(fome.sprites[8],(4*tile,0))
    else:
        screen.blit(fome.image,(4*tile,0))

    # modo de pesca
    if naufrago_vision.distancia == 'curta':
        screen.blit(modo_pesca[0],(0,4*tile))
    else:
        screen.blit(modo_pesca[1],(0,4*tile))

    # textos ------------------------------------------------------------------------

    # peixe
    qnt_peixes_texto = fonte.render(f'{qnt_peixe}', False, 'White')
    screen.blit(qnt_peixes_texto, (0.5*tile, 0.1*tile))

    # madeira
    qnt_madeira_texto = fonte.render(f'{qnt_madeira}', False, 'White')
    screen.blit(qnt_madeira_texto, (0.5*tile, 0.6*tile))

    # dias
    dias_texto = fonte.render(f'{qnt_dias}', False, 'White')
    dias_rect = dias_texto.get_rect(topright=(4.5*tile, 4.65*tile))
    screen.blit(dias_texto, dias_rect)

    # debug
    debug = tempo  # alterar a variavel para escolher o que vai ser mostrado
    texto_debug = fonte_menor.render(f"tempo: {debug}", False, 'Red')
    # screen.blit(texto_debug, (2.5*tile-(len(str(debug))/2*10.48), 0.1*tile))

    # animação bg logo --------------------------------------------------------------

    # retirando background da logo
    logo_bg_x += 7
    logo_bg_y += 7
    if logo_bg_x < 700: screen.blit(logo_bg,(logo_bg_x,logo_bg_y))
    
    # UPDATE DA TELA E RELÓGIO(FPS) ---------------------------------------------------
    pg.display.update()
    clock.tick(40)
