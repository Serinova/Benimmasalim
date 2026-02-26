# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies + fonts (page_composer metin çizimi için şart)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgl1 \
    libglib2.0-0 \
    fonts-liberation \
    fonts-dejavu-core \
    fontconfig \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Google Fonts — admin panelde seçilebilen tüm fontları GitHub'dan indir
# Variable font (.ttf) dosyalarını doğrudan raw.githubusercontent.com'dan çek
RUN mkdir -p /usr/share/fonts/truetype/google && cd /usr/share/fonts/truetype/google && \
    # Nunito (variable)
    curl -sfL -o Nunito.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/nunito/Nunito%5Bwght%5D.ttf" && \
    # Quicksand (variable)
    curl -sfL -o Quicksand.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/quicksand/Quicksand%5Bwght%5D.ttf" && \
    # Comfortaa (variable)
    curl -sfL -o Comfortaa.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/comfortaa/Comfortaa%5Bwght%5D.ttf" && \
    # Baloo 2 (variable)
    curl -sfL -o Baloo2.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/baloo2/Baloo2%5Bwght%5D.ttf" && \
    # Bubblegum Sans (static)
    curl -sfL -o BubblegumSans-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/bubblegumsans/BubblegumSans-Regular.ttf" && \
    # Comic Neue (static)
    curl -sfL -o ComicNeue-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/comicneue/ComicNeue-Regular.ttf" && \
    # Patrick Hand (static)
    curl -sfL -o PatrickHand-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/patrickhand/PatrickHand-Regular.ttf" && \
    # Caveat (variable)
    curl -sfL -o Caveat.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/caveat/Caveat%5Bwght%5D.ttf" && \
    # Lobster (static)
    curl -sfL -o Lobster-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/lobster/Lobster-Regular.ttf" && \
    # Pacifico (static)
    curl -sfL -o Pacifico-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/pacifico/Pacifico-Regular.ttf" && \
    # Fredoka (variable — eski adı Fredoka One)
    curl -sfL -o Fredoka.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/fredoka/Fredoka%5Bwdth%2Cwght%5D.ttf" && \
    # Bangers (static)
    curl -sfL -o Bangers-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/bangers/Bangers-Regular.ttf" && \
    # Chewy (static — apache lisanslı)
    curl -sfL -o Chewy-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/apache/chewy/Chewy-Regular.ttf" || \
    curl -sfL -o Chewy-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/chewy/Chewy-Regular.ttf" || true && \
    # Luckiest Guy (static)
    curl -sfL -o LuckiestGuy-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/apache/luckiestguy/LuckiestGuy-Regular.ttf" || \
    curl -sfL -o LuckiestGuy-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/luckiestguy/LuckiestGuy-Regular.ttf" || true && \
    # Poppins (static — Regular ağırlık)
    curl -sfL -o Poppins-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf" || true && \
    # Montserrat (variable)
    curl -sfL -o Montserrat.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf" || true && \
    # Open Sans (variable)
    curl -sfL -o OpenSans.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/opensans/OpenSans%5Bwdth%2Cwght%5D.ttf" || true && \
    # Roboto (apache lisanslı, variable)
    curl -sfL -o Roboto.ttf "https://raw.githubusercontent.com/google/fonts/main/apache/roboto/Roboto%5Bwdth%2Cwght%5D.ttf" || \
    curl -sfL -o Roboto.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/Roboto%5Bwdth%2Cwght%5D.ttf" || true && \
    # --- Yeni eklenen fontlar ---
    # Indie Flower (el yazısı)
    curl -sfL -o IndieFlower-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/indieflower/IndieFlower-Regular.ttf" || true && \
    # Shadows Into Light
    curl -sfL -o ShadowsIntoLight-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/shadowsintolight/ShadowsIntoLight.ttf" || true && \
    # Pangolin
    curl -sfL -o Pangolin-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/pangolin/Pangolin-Regular.ttf" || true && \
    # Gaegu (variable)
    curl -sfL -o Gaegu-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/gaegu/Gaegu-Regular.ttf" || true && \
    # Sniglet
    curl -sfL -o Sniglet-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/sniglet/Sniglet-Regular.ttf" || true && \
    # Itim
    curl -sfL -o Itim-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/itim/Itim-Regular.ttf" || true && \
    # Schoolbell
    curl -sfL -o Schoolbell-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/apache/schoolbell/Schoolbell-Regular.ttf" || \
    curl -sfL -o Schoolbell-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/schoolbell/Schoolbell-Regular.ttf" || true && \
    # Gloria Hallelujah
    curl -sfL -o GloriaHallelujah-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/gloriahallelujah/GloriaHallelujah.ttf" || true && \
    # Amatic SC
    curl -sfL -o AmaticSC-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/amaticsc/AmaticSC-Regular.ttf" || true && \
    # Satisfy
    curl -sfL -o Satisfy-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/apache/satisfy/Satisfy-Regular.ttf" || \
    curl -sfL -o Satisfy-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/satisfy/Satisfy-Regular.ttf" || true && \
    # Righteous
    curl -sfL -o Righteous-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/righteous/Righteous-Regular.ttf" || true && \
    # Architects Daughter
    curl -sfL -o ArchitectsDaughter-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/architectsdaughter/ArchitectsDaughter-Regular.ttf" || true && \
    # Kalam
    curl -sfL -o Kalam-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/kalam/Kalam-Regular.ttf" || true && \
    curl -sfL -o Kalam-Bold.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/kalam/Kalam-Bold.ttf" || true && \
    # Delius
    curl -sfL -o Delius-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/delius/Delius-Regular.ttf" || true && \
    # Handlee
    curl -sfL -o Handlee-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/handlee/Handlee-Regular.ttf" || true && \
    # Just Another Hand
    curl -sfL -o JustAnotherHand-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/justanotherhand/JustAnotherHand.ttf" || true && \
    # Reenie Beanie
    curl -sfL -o ReenieBeanie-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/reeniebeanie/ReenieBeanie.ttf" || true && \
    # Sue Ellen Francisco
    curl -sfL -o SueEllenFrancisco-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/sueellenfrancisco/SueEllenFrancisco.ttf" || true && \
    # Short Stack
    curl -sfL -o ShortStack-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/shortstack/ShortStack-Regular.ttf" || true && \
    # Coming Soon
    curl -sfL -o ComingSoon-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/apache/comingsoon/ComingSoon-Regular.ttf" || true && \
    # Covered By Your Grace
    curl -sfL -o CoveredByYourGrace-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/coveredbyyourgrace/CoveredByYourGrace.ttf" || true && \
    # Permanent Marker
    curl -sfL -o PermanentMarker-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/apache/permanentmarker/PermanentMarker-Regular.ttf" || true && \
    # fontconfig cache yenile
    fc-cache -fv 2>/dev/null || true && \
    ls -la /usr/share/fonts/truetype/google/

# Create non-root user with writable home directory
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --home /home/appuser --ingroup appgroup appuser

ENV HOME=/home/appuser

# Copy wheels and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application
COPY --chown=appuser:appgroup . .

# Make start script executable (before switching user)
RUN chmod +x /app/start.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Start with migration + gunicorn
CMD ["/bin/bash", "./start.sh"]
