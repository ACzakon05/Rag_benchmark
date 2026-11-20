# Specyfikacja API KrakCloud v3

## 1. Limity zapytań (Rate Limiting)

### 1.1 Plan Starter
Klucze API w planie Starter mogą wykonywać do 60 zapytań na minutę oraz maksymalnie 50 000 wywołań miesięcznie. Przekroczenie limitu zwraca status HTTP 429 z kodem KC-4291.

### 1.2 Plan Pro
Klucze API w planie Pro pozwalają na 600 zapytań na minutę oraz 1 000 000 wywołań miesięcznie. Dodatkowo dostępny jest mechanizm burst do 900 zapytań przez 10 sekund.

### 1.3 Plan Enterprise
Klucze API w planie Enterprise oferują limit 5000 zapytań na minutę bez twardego limitu miesięcznego oraz dedykowaną pulę połączeń w regionie eu-central-1.

## 2. Kody błędów i ponawianie webhooków

### 2.1 Wybrane kody diagnostyczne
Kod KC-4291 sygnalizuje przekroczenie limitu zapytań na minutę; klient powinien odczytać nagłówek `Retry-After` i wstrzymać wysyłanie kolejnych żądań.

Kod KC-5038 oznacza chwilową niedostępność kolejki indeksowania dokumentów i wymaga ponowienia żądania z wykładniczym odstępem czasu.

### 2.2 Harmonogram ponowień webhooków
W przypadku odpowiedzi innej niż 2xx system ponawia dostarczenie webhooka łącznie 5 razy w odstępach: 1 minuta, 5 minut, 30 minut, 2 godziny oraz 12 godzin. Po piątej nieudanej próbie subskrypcja zostaje zawieszona i wysyłane jest powiadomienie e-mail do administratora konta.