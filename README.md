# Informatie

De opdracht is namelijk om een tool te ontwikkelen waarme de aanwezigheid van studenten bijgehouden kan worden tijdens de studie.

Het bijhouden van de aanwezigheid van studenten is een belangrijk aspect van het onderwijs. Het stelt docenten in staat om een beter beeld te krijgen van het studiegedrag van hun studenten en eventueel bij te sturen waar nodig.

Het is belangrijk dat de tool gebruiksvriendelijk en efficiënt is, zodat docenten er makkelijk mee kunnen werken en er waardevolle informatie uit kunnen halen.

# Vereisten

Als student:

- [x] wil ik een check-in kunnen maken
- [x] check-in van een eerder moment onthouden
- [x] kan je ook zonder QR code inloggen
- [ ] niet mogelijk om de check-in te vervalsen

Als docent:

- [x] welke studenten in onze bijeenkomst aanwezig zijn
- [x] welke studenten nog niet aanwezig zijn
- [x] welke studenten hebben zich afwezig gemeld
- [x] hoeveel studenten zich hebben ingecheckt
- [ ] apart scherm om de check-in te kunnen openen
- [ ] per bijeenkomst een aanvullende vraag
- [ ] les tevoren plannen en aangeven wanneer deze start en eindigt
- [ ] wie aanwezig was en hoe laat deze zich heeft ingecheckt en wie was afgemeld
- [ ] wil per student zien in welke lessen in het verleden heeft ingecheckt

Als beheerder:
- [ ] manier om snel klassen te kunnen invoegen
- [ ] veel informatie is niet vereist alleen naam en studentnummer

API:
- [ ] REST API basis crud elementen kan gebruik maken van swagger

Technische eisen:
- [x] RAC huisstijl
- [ ] REST URLS niet zonder authenticatie
- [ ] Tenminste het overzichtsscherm van docent real-time verversen
- [x] Backend python met Flask SQLITE
- [x] ERD en database. De ERD moet eenduidig zijn
- [x] SQLITE wordt aangeraden


# Structure
Starter repository voor Werkplaats 3. Deze repository bevat een Flask applicatie met een aantal van de componenten die we ook nodig hebben om de werkplaats opdracht uit te voeren: 
- Een database
- Templates
- De Flask server
- HTML & Style sheets

# Installatie en setup
Om Flask te kunnen starten zul je eerst de Flask packages moeten installeren. Wil je latere problemen met versies voorkomen, dan raden we je aan een virtual environment te maken en daar de modules in te 
installeren:  

```
pip install virtualenv

virtualenv venv

.\venv\sripts\activate

pip install -r requirements.txt
```
Om de demo applicatie te starten: 
``` 
.\venv\sripts\activate

python main.py
```

# Gebruikte software
- Python
- Flask
- Ajax
- JQuery
- JavaScript
- Bootstrap
- HTML
- CSS

# Credits

Thijs, Erik, Martijn
