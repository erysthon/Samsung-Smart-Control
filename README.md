# Reutilizando o controle

### Sim isso é possível...

&#8195;A idéia me veio quando minha tv quebrou e eu comecei a pensar em como poderia reaproveitá-la, foi então que olhei para o controle e pensei será? O dispositivo tem uma boa qualidade e funciona via bluetooth, por isso havia uma faísca de esperança.

### Avisos

* **Não garanto** que seu controle vá funcionar perfeitamente com os arquivos deste repositório, de acordo com o modelo, seu dispositivo pode enviar sinais distintos do que usei em meus testes e **dependendo do seu empenho** pode ser necessário fazer mudanças para que funcione a partir deste projeto.

* **Não me responsabilizo** por qualquer **dano** que você possa causar ao seu hardware, todo o processo aqui foi **testado por mim** e funcionou em meu cenário. Faça por **sua conta e risco**.

### Meu ambiente 
* Hardware: Samsung Smart Control **RMCSPR1AP1**
* Sistema operacional: **Arch Linux**

# Tutorial

### Conectando o controle via bluetooth

&#8195;Aqui enfrentamos um problema os controles da Samsung usam a tecnologia **BLE - Bluetooth Low Energy** então se você simplesmente conectar o controle via bluetooth ele pode ficar **conectando e desconectando** varias vezes, sem conseguir manter uma conexão sólida. Isso ocorre porque controle tenta estabelecer uma conexão, o "aperto de mão" (handshake) **falha** ou o sistema de economia de energia o **derruba**, e ele entra nesse loop infinito de conecta/desconecta. Para resolver isso **é necessário configurar o Bluetooth, limpar as conexões salvas no controle e conectá-lo via terminal**.

* Configurando o Bluetooth:

&#8195;&#8195;&#8195;1. Edite o arquivo de configuração do bluetooth: `sudo nano /etc/bluetooth/main.conf`

&#8195;&#8195;&#8195;2. Na seção **[General]** adicione ou altere essas linhas:
```
Class = 0x000100
FastConnectable = true
JustWorksRepairing = always
```

&#8195;&#8195;&#8195;3. Na seção **[LE]** adicione ou altere essas linhas:
```
MinConnectionInterval=6
MaxConnectionInterval=9
ConnectionLatency=0
```

&#8195;&#8195;&#8195;4. No terminal execute:

```
sudo systemctl stop bluetooth
sudo modprobe uhid
sudo modprobe -r btusb
sudo modprobe btusb
sudo modprobe uinput
sudo modprobe hid_samsung
sudo modprobe hid-generic
sudo modprobe btusb enable_autosuspend=0
echo "options btusb enable_autosuspend=0" | sudo tee /etc/modprobe.d/bluetooth.conf
sudo systemctl start bluetooth
```

* Limpando conexões: **Remova** as pilhas do controle e **pressione** o botão de ligar por 30 a 45 segundos.

* Conectando via terminal: Após limpar as conexões, abra o terminal e execute nesta sequência:

&#8195;&#8195;&#8195;1. `bluetoothctl`

&#8195;&#8195;&#8195;2. `power on`

&#8195;&#8195;&#8195;3. `agent NoInputNoOutput`

&#8195;&#8195;&#8195;4. `default-agent`

&#8195;&#8195;&#8195;5. `pairable on`

&#8195;&#8195;&#8195;6. `scan on` (neste momento é necessário que você coloque o controle em **modo de pareamento**, no meu controle isso é possível segurando os botões **voltar** e **play/pause**, dependendo do seu controle isso **pode variar**. Nesta etapa é importante copiar o Mac do dispositivo para os próximos passos).

&#8195;&#8195;&#8195;7. `pair XX:XX:XX:XX:XX:XX` (**IMPORTANTE**: No momento em que você der o comando `pair`, **mantenha** o modo de pareamento. Se você **parar** de apertar, o controle entra em sleep e dá o **erro** de Timeout. Se ele pedir um PIN no terminal, o que é raro, mas acontece, digite 0000 ou 1234. Se ele responder `Confirm passkey... (yes/no)`, digite **yes** imediatamente).

&#8195;&#8195;&#8195;8. `trust XX:XX:XX:XX:XX:XX`

&#8195;&#8195;&#8195;9. `connect XX:XX:XX:XX:XX:XX`

&#8195;&#8195;&#8195;10. Se após executar o connect o terminal retomar: `[CHG] Device XX:XX:XX:XX:XX:XX ServicesResolved: yes` e o dispositivo continuar conectado por mais de **30 segundos** então a conexão foi estabelecida com sucesso, você pode parar de pressionar os botões e agora só precisamos mapear os comandos.

### Mapeando os botões 

#### Identificando os sinais

&#8195;Antes de continuarmos precisamos verificar se os sinais estão sendo enviados corretamente e quais sinais estão sendo recebidos. Para isso podemos usar o evtest:

* Instalando o evtest: ```sudo pacman -S evtest```

* Executando o evtest: ```sudo evtest```

&#8195;No evtest verifique se o controle aparece, o nome pode variar mas será algo como `Smart Control`. Em meu computador foram detectados 4 eventos enviados pelo controle:
```
No device specified, trying to scan all of /dev/input/event*
Available devices:
/dev/input/event10:    Smart Control 2016 Keyboard
/dev/input/event11:    Smart Control 2016 Mouse
/dev/input/event12:    Smart Control 2016
/dev/input/event13:    Smart Control 2016
Select the device event number [0-13]: 
```

&#8195;Neste momento é muito importante que você teste cada event. Por meio dos testes descobri que meu controle envia a resposta dos botões no `event 12`. Para testar é bem fácil, selecione um event e aperte os botões do controle, se não obtiver resposta, feche o evtest, execute-o novamente e teste em outro event. Quando descobrir o event correto o terminal deverá dar uma resposta parecida com essa ao apertar os botões:
```Event: time 1770850376.938658, type 2 (EV_REL), code 9 (REL_MISC), value 2```

&#8195;Aqui podemos observar algumas informações interessantes, eu usei o botão de ligar como exemplo e ao apertar o controle está enviando um sinal do **tipo 2** com **código 9** e **valor 2**. Se pegarmos o botão central para comparar vamos obter isso:
```Event: time 1770850578.754669, type 2 (EV_REL), code 9 (REL_MISC), value 104```

&#8195; Nota-se que o tipo e o código permanecem os mesmos, o que muda é apenas o **valor**. Como cada modelo pode enviar sinais diferentes, eu recomendo que anote as informações de cada botão, pois talvez seja necessário alterar algo posteriormente com base nesses valores.

#### Permissões e dependências

&#8195;Para mapearmos precisaremos criar um script que identifique o sinal do controle e converta para uma resposta no computador, mas antes de criarmos esse script precisamos garantir que temos as permissões e as dependências necessárias para que este script funcione: 

* Adicionando permissões:
```
sudo groupadd uinput
sudo usermod -aG input,uinput $USER
echo 'KERNEL=="uinput", GROUP="uinput", MODE="0660", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-uinput.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

* Instalando dependências:
&#8195;Para que o script funcione precisaremos instalar as dependências `evdev` e `uinput`, no Arch esses pacotes estão disponíveis no aur, aqui está um exemplo usando o yay, use o aur helper de sua preferência:
```yay -S python-evdev python-uinput```

#### Criando o script
&#8195;Para mapearmos corretamente os botões usaremos um script em python que será executado sempre que o controle for conectado, neste repositório você pode encontrar 2 arquivos: [samsung_remap.py](samsung_remap.py) e [samsung-remote.service](samsung-remote.service).

&#8195;&#8195;&#8195;1. Cole o conteúdo de [samsung_remap.py](samsung_remap.py) em `/usr/local/bin/samsung_remap.py`

&#8195;&#8195;&#8195;2. Cole o conteúdo de [samsung-remote.service](samsung-remote.service) em `sudo nano /etc/systemd/system/samsung-remote.service`

&#8195;&#8195;&#8195;3. Execute no terminal:
```
echo 'KERNEL=="event*", ATTRS{name}=="Smart Control", TAG+="systemd", ENV{SYSTEMD_WANTS}="samsung-remote.service"' | sudo tee /etc/udev/rules.d/99-samsung-remote.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### Configurações
&#8195;A maioria das configurações relevantes serão encontradas no [samsung_remap.py](samsung_remap.py), ele é quem está encarregado de fazer o mapeamento, das configurações podemos ressaltar: 

* Configuração de timeout: [DEBOUNCE_TIME = 0.2](samsung_remap.py#L9) (essa configuração é necessária pois o controle envia dois sinais para um clique de botão, o que evita erros caso um sinal se perca, se não houver timeout ocorrerá um clique duplo).

* Configurações de funções: [def power_off():](samsung_remap.py#L12) (como estamos usando um script em python para mapear o controle podemos criar funções específicas e definir para qualquer botão).

* Mapeamento dos botões: [mapping =](samsung_remap.py#L19) (aqui está mapeado cada botão, para alterar a função de algum botão basta alterar esse segmento do código).

### Notas

* Esse projeto é apenas algo experimental para tentar **reaproveitar** um hardware que iria para o **lixo**, não estou incentivando ninguém a fazê-lo, se você acha que consegue e que terá utilidade para você é com você.

* Não encontrei na internet outros tutoriais que ajudem a fazer isso. Espero que consiga ajudar alguém que possa **tirar proveito** de um controle, dependendo do seu empenho pode ser algo muito **útil** devido a qualidade do controle e da possibilidade de atribuir quaisquer funções a qualquer botão.
