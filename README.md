# CBOT
<h3 align="center">CBOT, Discord sunucularında ders yönetimini kolaylaştıran bir bot yazılımıdır. </h3>
<img align="left" width="250" height="250" src="https://user-images.githubusercontent.com/100694366/229351915-05326b39-e81f-4e48-bc3f-2f176a27ad91.png">
<h3 align="left">Özellikleri:</h3>
<ul>
  <li>Temel Fakülte kanalı oluşturma.</li>
  <li>Kullanıcı doğrulama sistemi. (E-posta)</li>
  <li>Bölüm ve ders rollerinin yaratılması.</li>
  <li>Dersler için katılımcılara göre kanalların otomatik yaratılması.</li>
  <li>Kullanıcıların ders kanallarına ve rollerine otomatik erişimi.</li>
  <li>Öğrenci ve öğretmen rollerini atanması ve yetkilendirilmesi.</li>
  <li>Anonim duyuru yapabilme.</li>  
</ul>

Özel olarak <a href="https://muh.baskent.edu.tr/kw/index.php">Başkent Üniversitesi Mühendislik Fakültesi</a> için tasarlanmıştır.


## System Design
CBOT utilizes both Service Oriented Architecture (SOA) and Event-Driven
Architecture (EDA) in its design. SOA is used to encapsulate the various functions of
CBOT into individual services, while EDA is used to respond to and process events from
the Discord API. This combination allows CBOT to be modular, scalable, and responsive
to changes in the environment.
Each service in CBOT listens to certain events according to its own needs, which is a
characteristic of event-driven architecture. At the same time, CBOT's services are
designed to work independently and communicate with each other through well-defined
interfaces, which is a characteristic of service-oriented architecture.

### Service Oriented Architecture (SOA)
![SOA](https://github.com/CanavarB/CBOT/assets/100694366/0b94f858-9fff-462a-854a-4f9a2a09658f)

### Event-Driven Architecture (EDA)
![EDA](https://github.com/CanavarB/CBOT/assets/100694366/5a0b6236-872a-4906-8d08-654022852325)


