import random #rastgele konum ve renkleriçin 
import tkinter as tk #grafiksel kullanıcı arayüzü GUI,Pencere, tuval vs. çizmek için
from dataclasses import dataclass

# Yılanın gövdesini verimli yönetmek içinLinked List Yapıları:------------------------------------------------------

class Node: #Tek bir düğüm (yılanın bir parçası) sınıfı
    def __init__(self, data):  # data: (x, y) konumu tutar
        self.data = data #Düğümün taşıdığı konum bilgisini saklar
        self.next = None

class SinglyLinkedList: #Yılanın tüm gövdesini bu yapıda tutucaz
    def __init__(self):
        self.head = None #Listenin baş düğümü (yılanın başı)
        self.tail = None #Listenin son düğümü (yılanın kuyruğu)
        self._len = 0 #Listedeki düğüm sayısı başlangıçta 0

    def __len__(self):
        return self._len

    def is_empty(self): # liste boş mu değil mi kontrol eder
        return self._len == 0
#Her kare ilerleme: push_front(yeni_baş) eklenir
    def push_front(self, data): #Listenin başına (yılanın başına) yeni bir parça ekler.Oyun mantığında “yılan bir kare ilerlediğinde” yeni baş konumu eklenir
        node = Node(data)         
        if self.head is None:
            self.head = self.tail = node
        else:
            node.next = self.head
            self.head = node
        self._len += 1 #Uzunluk 1 artar.
#Yem YOKSA: pop_back() ile kuyruk silinir (uzunluk sabit).Yem VARSA: pop_back() yapılmaz (yılan uzar)
    def pop_back(self): #yemeyi yemedği zaman self._len+=1 yapmaması için bu kısım çalışır
        if self.tail is None:
            raise IndexError("pop from empty list")
        if self.head is self.tail:
            data = self.tail.data
            self.head = self.tail = None
            self._len -= 1
            return data
        prev = self.head
        while prev.next is not self.tail:
            prev = prev.next
        data = self.tail.data
        prev.next = None
        self.tail = prev
        self._len -= 1
        return data

    def contains(self, pos): #yılanın kendine çarpıp çarpmadığını anlamak için kullanılır
        cur = self.head # çarptı baştan başlatır
        while cur: 
            if cur.data == pos:
                return True
            cur = cur.next
        return False

    def iter_nodes(self):
        cur = self.head
        while cur:
            yield cur
            cur = cur.next

    def tail_data(self):
        return None if self.tail is None else self.tail.data

# Oyun Ayarları------------------------------------------------------------------------------------------
CELL = 30 #Her ızgara karesinin piksel boyutu. Amacı çizim ve koordinat dönüştürmeyi kolaylaştırmak
COLS = 30 #sütun
ROWS = 30 #satır
WIDTH = COLS * CELL #900 px
HEIGHT = ROWS * CELL #900 px

# yılan hızı (milisaniye)
TICK_MS_BASE = 120 #değr düştükçe hız artar 

# Power-up süreleri (ms)
SLOW_MS_ADD = 120       # yavaşlatmada eklenen gecikme /geçici yavaşlatma mavi yem için
SLOW_DURATION = 5000    # 5 sn geçici yavaşlatmanın süresi
DOUBLE_DURATION = 30000 # 30 sn sarı yem double skor süresi

SCORE_PER_FOOD = 10  # normal yem sarı yemde bu değer 2x

# Yem ömrü (ms)
FOOD_DESPAWN_MS = 10000

# Renkler
# Renkler (dama arka plan)
BG1 = "#e8c7f1"
BG2 = "#f7ecff"
BG = BG1          # canvas arkaplanı (kareleri zaten boyayacağız)
GRID = "#2a2a2a"

# Yem ve power-up renkleri
COLOR_NORMAL = "#dc3232"   # normal yem rengi(kırmızı)
COLOR_SLOW = "#3a88ff"     # yavaşlatma yem rengi(mavi)
COLOR_DOUBLE = "#ffd54a"   # çift skor yem rengi (altın)
COLOR_POISON = "#b34dff"   # zehirli yem rengi(mor)

# Yönler (x,y)
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT} #zıt yöne gitmayi engellemek için


@dataclass
class GameState:#oyunun tüm dinamik durumunu tek yerde tutar 
    direction: tuple #tupleımız yılanın yönü
    next_direction: tuple #yeni yön girdisi
    snake: SinglyLinkedList #yılan gövdesi
    score: int #toplam puan
    paused: bool #geçici duraklatma
    game_over: bool #oyun sonu

# Yardımcılar-------------------------------------------------------------------------------------------
def grid_rand_empty(snake: SinglyLinkedList): #yemi yılan dışında bir kutuya koymak için kullanılır
    while True: #uygun hücre bulana kadar döngü döner
        pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1)) #yemi kutuya koymak için random x ve y koordinatı seçer
        if not snake.contains(pos):# seçtiği hücre yılanın üstünde değilse 
            return pos #yemi koyar 


def init_game_state(): #retry kısmı
    snake = SinglyLinkedList() #boş yılan oluşturur
    mid = (COLS // 2, ROWS // 2) #boş yılanı orta konuma yerleştirmek için(yılanın orta bölümü 30/2 30/2 lik konuma yerleştirilir)

    snake.push_front((mid[0] - 2, mid[1]))  # kuyruk konumu
    snake.push_front((mid[0] - 1, mid[1]))  # gövde konumu
    snake.push_front((mid[0], mid[1]))      # baş konumu

    return GameState(
        direction=RIGHT, #başlangıç yönü sağ
        next_direction=RIGHT, #ilk haraket yönü
        snake=snake,
        score=0 #başlangıç puanı
        ,paused=False #durdurulmamış
        ,game_over=False #bitmemiş oyun
    )


def collides_with_body(snake: SinglyLinkedList, new_head, will_eat: bool):#yılanın kendine çarptığında oyunu sonlandırmak için 
    cur = snake.head#cur ile tek tek düğümleri gezip listenin başına işaretçi koyar
    while cur:
        if (not will_eat) and (cur.data == snake.tail_data()):#bu hamlede yem yenmicekse ve yılanın başı kuyruğun eski konumuna geldiğinde oyun bitmez çünkü kuyruk ordan çekilmiş olur
            cur = cur.next
            continue
        if cur.data == new_head:#kendine çarpma kontrolü
            return True
        cur = cur.next#bağlı listedeki sonraki düğüm
    return False#çarpışma olmadıysa false döner ve oyun devam eder

# Tkinter tabanlı Oyun
class SnakeApp:#snake uygulamasını tanımlar
    def __init__(self, root: tk.Tk):#zamanlayıcı,tuş bağları ve oyun durumu burda kurulur
        self.root = root
        self.root.title("Snake (30x30) - Linked List - Tkinter") #pencere boyutunu ayarlar

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BG, highlightthickness=0)#oyuna alanın boyutunu ve arka plan rengini oluşturur
        self.canvas.pack()#ekrana yerleştirir

        self.status = tk.Label(root, text="", fg="white", bg="#111111", font=("Consolas", 12), anchor="w")#alt kısmında skor,durum,pause ,game over yazıları için etiket
        self.status.pack(fill="x")

        self.gs = init_game_state()#oyun durumunu kuran fonksiyon çağrılır  
        self._after_id = None#şu an aktif bir zamanlayıcı yok after çağrılınca ID atanır
        self.running = False#Oyunun döngüsü aktif mi diye kontrol eder
        self.show_intro = True#giriş ekranı mesajı gösteriyo mu

        # Dinamik tick
        self.current_tick_ms = TICK_MS_BASE#oyun hızını belirleyen tick süresi milisaniye türünden 

        # Power-up durumları bu durumlar slow ve double efektlerinin kalan süresini milisaniye olarak tutar ve her döngüde azaltılıp 0 a düşünce efekt biter
        self.slow_ms_remaining = 0
        self.double_ms_remaining = 0

        # Aktif item (tek slot): dict(type, pos, color)
        self.item = None #oluşan itemi tutar
        self._spawn_new_item()#ilk itemi yaratır

        # Yılan rengi (her yemde değiştirilecek)
        self.snake_body_color = self._rand_bright_color()#yılanın gövdesine rastgele renk atar
        self.snake_head_color = self._lighten(self.snake_body_color, 40) #kafası gövdeden daha açık renk ayırt edilebilmesi için

        # Kısayollar
        root.bind("<Up>", lambda e: self.set_dir(UP)) #ok tuşları ile yön değiştirme
        root.bind("<Down>", lambda e: self.set_dir(DOWN))
        root.bind("<Left>", lambda e: self.set_dir(LEFT))
        root.bind("<Right>", lambda e: self.set_dir(RIGHT))
        root.bind("w", lambda e: self.set_dir(UP)) #WASD tuşları ile yön değiştirme
        root.bind("s", lambda e: self.set_dir(DOWN))
        root.bind("a", lambda e: self.set_dir(LEFT))
        root.bind("d", lambda e: self.set_dir(RIGHT))
        root.bind("p", lambda e: self.toggle_pause()) #pause aç-kapat
        root.bind("P", lambda e: self.toggle_pause())
        root.bind("r", lambda e: self.retry())#restart
        root.bind("R", lambda e: self.retry())
        root.bind("<Escape>", lambda e: self.quit())#çıkış

        root.bind("<Return>", lambda e: self._handle_return()) #başlangıçta oyun başlatır ve oyun bitiminde yeniden oyun başlatır çok amaçlı kullanılır
        root.bind("<space>", lambda e: self.stop()) #oyunu durdurmak için

        self.render() #ilk ekran çizimini yapar uygulama da açılınca boş pencere yerine intro çizilsin

    # --------- Renk yardımcıları ----------(parlak renk üretir)
    def _rand_bright_color(self):#80-255 arasında olmasının sebebi çok koyu renkleri azaltır 
        r = random.randint(80, 255) 
        g = random.randint(80, 255)
        b = random.randint(80, 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _lighten(self, hex_color, delta=40):#kafa rengini gövdeye göre daha açık yapmak için
        hex_color = hex_color.lstrip("#")
        r = min(255, int(hex_color[0:2], 16) + delta)
        g = min(255, int(hex_color[2:4], 16) + delta)
        b = min(255, int(hex_color[4:6], 16) + delta)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _randomize_snake_color(self):#yılanın rengini yem yedikten sonra random şekilde yeniden ayarlar
        self.snake_body_color = self._rand_bright_color()
        self.snake_head_color = self._lighten(self.snake_body_color, 40)

    # --------- Item/power-up yardımcıları ----------
    def _spawn_new_item(self):
        # Tip seçimi: normal(70%), slow(15%), double(10%), poison(5%)
        roll = random.random()
        if roll < 0.70:#normal yemin çıkma olasılığı
            typ, color = "normal", COLOR_NORMAL
        elif roll < 0.85:#mavi yemin çıkma olsaılığ
            typ, color = "slow", COLOR_SLOW
        elif roll < 0.95:#sarı yemin çıkma olasılığı
            typ, color = "double", COLOR_DOUBLE 
        else:#Mor yemin çıkma olasılığı 
            typ, color = "poison", COLOR_POISON

        pos = grid_rand_empty(self.gs.snake)#yılanın üstüne gelmeyecek boş bir hücre seçer
        self.item = {"type": typ, "pos": pos, "color": color, "ttl": FOOD_DESPAWN_MS} #ekranda bulunan aktif yemin türü,knumu,rengi ve ne kadar süre ekranda kalacağı belirlenir

    # ------------- Zamanlayıcı -------------
    def _safe_cancel(self):#iptal edilecek bir zamanlayıcı var mı kontrol eder boş yere işlem yaptırtmaz
        if self._after_id is not None:
            try:#pause-restart ve game over durumlarında zamanlayıcıyı iptal eder 
                self.root.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None #artık zamanlayıcı iptal edildi

    def _schedule_loop_if_needed(self):#gerekirse oyunun döngüsünü başlatan yardımcı fonksiyon
        if self.running and self._after_id is None:#self.running true ise oyun çalışıyor demektir self._after_id ise atanmış zamanlayıcı yok demektir
            self._after_id = self.root.after(self.current_tick_ms, self.loop)#oyun döngüsünü başlatır aynı anda başka bir döngü başlatılmasını engeller gerekirse iptal eder
        #eğer bu kod olmasaydı her startta yeni loop olurdu oyun giderek hızlanırdı aynı anda birden fazla loop olurdu ve kontrol edilemeyen buglar olurdu

    # ------------- Kontrol Aksiyonları -------------
    def _handle_return(self): #entera basınca ne olcağını seçer
        if self.show_intro or (not self.running and not self.gs.game_over):#True ise oyunu başlatır,oyun çalışmıyosa ama bitmediyse de yine start
            self.start()
        elif self.gs.game_over:#oyun bittiyse retry
            self.retry()

    def start(self):#eğer oyun bitmişse her şeyi sıfırlar(yeni oyun)
        if self.gs.game_over:
            self.gs = init_game_state()
        self.gs.paused = False#duraklamayı kapatır
        self.running = True#oyun akışı başlar
        self.show_intro = False#oyun restart olduğunda giriş ekranı birdaha gösterilmez
        self._schedule_loop_if_needed()#oyunu adım adım ilerlemesi için sıraya koyar
        self.render()#ekranı yeniden çizdirir

    def stop(self):#oyunu tamamen durdurmak için
        self.running = False#oyun akışını durdurur
        self._safe_cancel()#sıraya konmuş oyun akışını iptal eder yoksa oyun durmaz
        self.render()#durduğunu ekranda gösterir

    def retry(self):#her şeyi sıfırlar ve oyunu yeniden başlatır
        self.gs = init_game_state()#yılanın pozisyonunu ,skor gibi her şeyi baştan oluşturur
        self.gs.paused = False#oyun duraklatılmamış
        self.running = True#oyun tekrar başlar
        self.show_intro = False#giriş ekranı kapatılır
        self.slow_ms_remaining = 0#yavaşlatma efekti yok
        self.double_ms_remaining = 0#çift skor efekti yok
        self.current_tick_ms = TICK_MS_BASE#oyun hızını normale döndürür
        self._randomize_snake_color()#yılan rengi rastgele değişir
        self._spawn_new_item()#yeni yem ve power-uplar gelir
        self._safe_cancel()#eski zamanlanmış döngü varsa iptal eder
        self._schedule_loop_if_needed()#yeni oyun döngüsünü başlatır
        self.render()#ekran yeniden çizilir

    def set_dir(self, d):#geçerli bir yönse kaydeder (d=yeni yön)
        if d != OPPOSITE.get(self.gs.direction, None):#zıt yönleri tanımlar
            self.gs.next_direction = d #yön değiştirir ama zıt yöne anında dönmeyi engeller

    def toggle_pause(self):#duraklamayı açıp kapatır
        if not self.gs.game_over:#oyun bitmediyse pause aç-kapat
            self.gs.paused = not self.gs.paused#oyun bittiyse pause ile uğraşmaz

    def quit(self):#güvenli çıkış
        self.running = False#oyunu durdurur
        self._safe_cancel()#zamanlanmış şeyleri iptal eder
        self.root.quit()#programı kapatır

    # ------------- Oyun Mantığı -------------
    def step(self):#oyunun bir adımını çalıştıran fonksiyon
        if self.gs.game_over or self.gs.paused:#pause de veya game over da yılan hareket etmez
            return

        # Etkilerin sürelerini güncelle
        self._tick_effect_timers()#efektleri sonsuza kadar sürmesin, süresi biten efektleri kapatır

        # Item ömrünü günceller (10 sn sonra despawn ve yeniden doğ)
        self._tick_item_timer()#yem ulaşılmaz bir yerde kalırsa oyun tıkanmaz

        # Yön güncelle
        if self.gs.next_direction != OPPOSITE.get(self.gs.direction, None):#mevcut yönün tersine dönmesini engeller
            self.gs.direction = self.gs.next_direction#eğer yön tersine değilse yeni yön , aktif yön olur

        #  Yılanın hareketi kafayı bir hücre ileri koymak ile başlar
        hx, hy = self.gs.snake.head.data#yılanın kafasının x ve y kordinaatları
        dx, dy = self.gs.direction#yön vektörü
        new_head = (hx + dx, hy + dy)#yeni kafa pozisyonu(yılanın kafası bir kare ileri gider)

        # Duvar çarpışması
        if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS): #eğer kafa duvara çarparsa oyun biter
            self._game_over_now()
            return

        # Bu adımda yem var mı?
        will_eat = self.item and (new_head == self.item["pos"])#yılanın kafası yemin üstüne gelirse yem yenir(will_eat=True)

        # Gövde çarpışması(yeni kafa yılanın gövdesinin üstüne geliyosa oyun biter)
        if collides_with_body(self.gs.snake, new_head, will_eat):#kuyruğun uzayıp uzamayacağını hesaba katar
            self._game_over_now()
            return

        # Yılanı ilerlet
        self.gs.snake.push_front(new_head)#yılanın kafasına bir parça ekler yani yılan bir kare ileri gider

        if will_eat:#eğer yem yendiyse 
            # Renk değiştir
            self._randomize_snake_color()#yılanın rengi rastgele değişir

            typ = self.item["type"]#yenen yemin türü
            if typ == "normal":#eğer normal yemse
                self._apply_score(+SCORE_PER_FOOD)#yılan uzar skor artar
            elif typ == "slow":#eğer mavi yem ise(yavaşlatan yem)
                # yavaşlatma: geçici olarak tick büyüt
                self.slow_ms_remaining = SLOW_DURATION #oyunu yavaşlatır ve yarım puan verir
                # Skor da verelim (istersen kaldır): küçük ödül
                self._apply_score(+SCORE_PER_FOOD // 2)
            elif typ == "double":#eğer sarı yemse double puan verir
                self.double_ms_remaining = DOUBLE_DURATION
                self._apply_score(+SCORE_PER_FOOD)  # alımda da puan ver
            elif typ == "poison":#eğer mor yem ise(zehirli)
                # skor azalt ve yılanı kısalt (mümkünse)
                self._apply_score(-SCORE_PER_FOOD)#puan düşürür(-10)
                if len(self.gs.snake) > 1:#yılan en az az iki kare ise kıyruktan bir parça sil
                    try:
                        self.gs.snake.pop_back()#hata olursa oyun çökmesin diye pas geç
                    except Exception:
                        pass

    # Yeni item
            self._spawn_new_item() #yılan yemi yediyse yeni yem oluşturulur
        else:
            # Normal hareket: kuyruk at
            self.gs.snake.pop_back()#eğer yem yenmediyse yılan ileri gider ve uzunluğu aynı kalır

    def _apply_score(self, delta):# skoru arttıran - azaltan fonksiyon (eklenecek puan)
        if delta > 0 and self.double_ms_remaining > 0: #çift puan kontrolü
            delta *= 2
        self.gs.score += delta #skoru günceller
        if self.gs.score < 0: #skorun sıfırın altına düşmesini engeller
            self.gs.score = 0

    def _game_over_now(self): #oyun bitirme fonksiyonu
        self.gs.game_over = True #oyun bitti olarak işaretlenir
        self.running = False #oyun döngüsü durdurulur
        self._safe_cancel() #zamanlayıcı güvenli şekilde iptal edilir

    def _tick_effect_timers(self): #oyun hızını ve efekt sürelerini kontrol eder
        if self.slow_ms_remaining > 0: #slow efekti varsa ouyunu yavaşlatır
            self.current_tick_ms = TICK_MS_BASE + SLOW_MS_ADD #slow efekti yoksa oyun normal hızda devam eder
        else:
            self.current_tick_ms = TICK_MS_BASE

        # Zamanı azalt
        if self.slow_ms_remaining > 0: #slow efektinin süresi tick te azalır, sıfırın altına düşmez
            self.slow_ms_remaining = max(0, self.slow_ms_remaining - self.current_tick_ms)
        if self.double_ms_remaining > 0: #çift puan efektinin süresini kontrol eder
            self.double_ms_remaining = max(0, self.double_ms_remaining - self.current_tick_ms) #çift puan efektinin süresi azalır sıfırın altına düşmez
    def _tick_item_timer(self): #haritadaki yemin süresini kontrol eder
        if not self.item:#oyunda yem yoksa fonksiyonu hemen bitirir alttaki kodlar çalışmaz
            return
        self.item["ttl"] = self.item.get("ttl", FOOD_DESPAWN_MS) - self.current_tick_ms #yemin yaşam süresi azaltılır
        if self.item["ttl"] <= 0: #yemin süresi bittiyse 
            self._spawn_new_item()#eski yem silinir yeni yem oluşturulur  


    # ------------- Çizim -------------
    def draw_cell(self, pos, color, pad=2): #oyun alanındaki tek bir kareyi çizer
        x, y = pos #ızgara koordinatları
        x0 = x * CELL + pad #kare sol üst köşe piksel koordinatları
        y0 = y * CELL + pad
        x1 = x0 + CELL - 2 * pad#kare sağ alt köşe piksel koordinatları
        y1 = y0 + CELL - 2 * pad
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=color, width=1) #canvas üzerine renkli bir kare çizer

    def draw_grid(self):  # dama desenli arka plan
        for y in range(ROWS):
            for x in range(COLS):
                color = BG1 if (x + y) % 2 == 0 else BG2
                x0 = x * CELL
                y0 = y * CELL
                x1 = x0 + CELL
                y1 = y0 + CELL
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=color)
   
    def render_intro(self): #oyunun başlangıç ekranını çizer
        self.canvas.delete("all") #canvas üzerindeki her şeyi siler
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", outline="#000000") #arka planı komple doldurur
        title = "ERROR TEAMS GAME" # oyunun başlık yazısı
        info1 = "Başlamak için Enter'a basın" #oyun başlatma bilgisi
        info2 = "Durdurmak için Space'e basın" # oyun durdurma bilgisi
        info3 = "Yön: Ok Tuşları / WASD   |   R: Tekrar   |   ESC: Çıkış" #oyun yön tuşları bilgisi
        info4 = "Power-up'lar: Mavi=Yavaş, Altın=2x Skor (30sn), Mor=Zehir" # oyun power-up bilgisi
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2 - 36, text=title, fill="#ff69b4",  #oyun başlığı
                                font=("Consolas", 22, "bold"))
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2 - 2, text=info4, fill="#80c0ff", font=("Consolas", 12, "bold")) #"enter a bas"yazısını çizer
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2 + 24, text=info1, fill="#cccccc", font=("Consolas", 14)) #"space ile durdurur"yazısını çizer
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2 + 48, text=info2, fill="#cccccc", font=("Consolas", 14)) #kontrol tuşları bilgisi
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2 + 80, text=info3, fill="#888888", font=("Consolas", 10)) # power-up bilgisi
        self.status.config(text="Enter: Başlat  |  Space: Durdur  |  R: Tekrar") #alt durum çubuğuna bilgi yazar

    def render_game(self): #oyunun asıl oynanış ekranını çizer
        self.canvas.delete("all") #önce ekranı temizler
 
      
        self.draw_grid() #ızgarayı çizer

        # Item'ı çiz
        if self.item: # eğer haritada yem varsa
            self.draw_cell(self.item["pos"], self.item["color"], pad=3)#yemi kare olarak çizer

        # Yılanı çiz
        first = True #ilk kare yılanın başını temsil ediyor mu onu kontrol eder
        for node in self.gs.snake.iter_nodes(): #yılanın tüm parçalarını sırayla gezer
            self.draw_cell(node.data, self.snake_head_color if first else self.snake_body_color, pad=3) #eğer ilk parçaysa kafa rengi değilse gövde rengini alır,yılanın her parçasını kare olarak çizer
            first = False #ilk parça çizildikten sorna artık gövdeye geçilir

        # Status
        slow_txt = f"Slow:{self.slow_ms_remaining//1000:02d}s" if self.slow_ms_remaining > 0 else "Slow: -" # yavaşlatma efekti,bu efekt varsa efektin kalan süresini saniye olarak gösterir
        dbl_txt = f"2x:{self.double_ms_remaining//1000:02d}s" if self.double_ms_remaining > 0 else "2x: -" # çift puan efekti, bu efekt varsa efektin kalan süresini gösterir
        info = f"Score: {self.gs.score}  |  {slow_txt}  |  {dbl_txt}" #alt barda gösterilecek bilgi metnini hazırlar
        if self.gs.paused: #oyun duraklatıldıysa bilgiye eklenir
            info += "  |  Paused (P)" 
        if self.gs.game_over: #oyun bittiiyse tekrar bilgisi eklenir
            info += "  |  Game Over (R: Tekrar)"
        self.status.config(text=info) # alt durum çubuğundaki yazı durumu güncellenir

        # Game Over overlay
        if self.gs.game_over: #oyun bittiyse game over ekranı çizilir
            self.render_game_over_overlay() 

    def render_game_over_overlay(self): #oyun bittiğinde ekranın üstüne yarı saydam katman çizer
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", outline="", stipple="gray50") #oyunu karartır(siyah yarı saydam arka plan)
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2 - 20, text="GAME OVER", fill="#ff4444", #ortada game over yazısı
                                font=("Consolas", 26, "bold"))
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2 + 10, #skor yazısı
                                text=f"Score: {self.gs.score}", fill="#ffffff",
                                font=("Consolas", 14))
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2 + 36, #yeniden başlatma bilgisi
                                text="Tekrar oynamak için R'ye basın", fill="#000000",
                                font=("Consolas", 12)) 

    def render(self): #hangi ekranın çizileceğine karar verir
        if self.show_intro and not self.running and not self.gs.game_over: #eğer intro açık,oyun başlamamış,game over değilse
            self.render_intro() #başlangıç ekranı çizer
        else: # aksi halde oyun ekranını çizer
            self.render_game()

    # ------------- Döngü -------------
    def loop(self): #oyunun sürekli çalışan ana döngüsü
        if not self.running: #oyun çalışmıyorsa zamanlayıcıyı durdurur,döngüden çıkartır
            self._after_id = None
            return
        self.step() #oyunun bir adımını çalıştırır(yılan hareketi,çarpma,yem,skor gibi)
        self.render() # ekranı yeniden çiz
        # Bir sonraki loop'u güncel hıza göre planla
        self._after_id = self.root.after(self.current_tick_ms, self.loop) #sonsuz oyun döngüsü


def main(): #programın başlangıç noktası
    root = tk.Tk() #tkinter ana pencere oluşturulur
    app = SnakeApp(root) # sanke oyunu başlatılır
    root.mainloop() #pencere açık kaldığı sürece program çalışır


if __name__== "__main__": #dosya direkt çalıştırıldıysa,main()fonksiyonu çağırılır
    main()