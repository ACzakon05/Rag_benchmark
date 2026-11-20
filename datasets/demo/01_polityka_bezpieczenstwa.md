# Polityka Bezpieczeństwa Informacji KrakCloud

## 1. Zasady haseł i uwierzytelniania

### 1.1 Wymagania dla kont pracowników
Hasło do konta firmowego musi zawierać co najmniej 14 znaków, w tym wielką literę, cyfrę oraz znak specjalny. Zmiana hasła nie jest wymuszana cyklicznie, chyba że wykryto naruszenie poufności lub konto pojawiło się na liście wycieków.

### 1.2 Uwierzytelnianie wieloskładnikowe (MFA)
Dostęp do konsoli produkcyjnej oraz repozytoriów kodu wymaga sprzętowego klucza FIDO2 lub aplikacji TOTP; kody SMS nie są akceptowane od stycznia 2025 roku. Każde nowe urządzenie robocze musi zostać zarejestrowane w systemie MDM przed pierwszym logowaniem.

## 2. Klasyfikacja incydentów bezpieczeństwa

### 2.1 Incydent krytyczny (INC-P1)
Zdarzenie oznaczone kodem INC-P1 dotyczy wycieku danych klientów lub nieautoryzowanego dostępu do klastrów produkcyjnych. Zespół SOC musi podjąć reakcję w ciągu 15 minut od zgłoszenia, niezależnie od pory dnia.

### 2.2 Incydent wysoki (INC-P2)
Zdarzenie oznaczone kodem INC-P2 obejmuje naruszenie środowiska stagingowego lub masowe próby logowania z zablokowanych adresów IP. Czas reakcji zespołu SOC wynosi maksymalnie 2 godziny robocze.

### 2.3 Błędy autoryzacji VPN (ERR-AUTH-4032)
Kod błędu ERR-AUTH-4032 oznacza wygasły certyfikat klienta WireGuard na stacji roboczej. W takiej sytuacji należy odnowić certyfikat poleceniem `kc-vpn renew --force` w terminalu i ponownie zestawić tunel.