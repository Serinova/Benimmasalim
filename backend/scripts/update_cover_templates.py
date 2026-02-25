"""Update scenario cover_prompt_templates with location-specific and sky-space-aware templates."""
import asyncio
import sys
sys.path.insert(0, "/app")

from sqlalchemy import text
from app.core.database import async_session_factory

KAPADOKYA_COVER = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing on a rocky outcrop overlooking the magical landscape of Cappadocia, Turkey.

ICONIC BACKGROUND ELEMENTS (must include):
- Dozens of colorful hot air balloons floating gracefully in the golden sunrise sky
- Towering fairy chimneys in various mushroom and cone shapes with eroded caps
- Ancient cave dwellings carved into the soft volcanic tuff rock formations
- The distinctive Goreme Valley panorama stretching into the misty distance

LIGHTING & ATMOSPHERE:
- Magical golden hour sunrise light casting long warm shadows
- Soft morning mist swirling between the fairy chimneys
- Warm earth tones: terracotta, sandy beige, dusty rose, golden ochre

CLOTHING:
The child is wearing {clothing_description}.

COMPOSITION REQUIREMENTS:
- Child positioned in lower third of the image
- Upper 30% is clear sky with hot air balloons, open space for title text overlay
- Balanced composition with fairy chimneys framing the scene
- Sense of wonder and adventure

No text, no letters, no words in the image."""

YEREBATAN_COVER = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, exploring deep inside the magnificent underground Yerebatan Cistern (Basilica Cistern) in Istanbul, Turkey.

ICONIC BACKGROUND ELEMENTS (include 2-3 key details):
- Hundreds of ancient marble columns stretching into the distance, reflected in the shallow water below
- Warm amber and orange lighting illuminating the underground space with dramatic shadows
- The famous Medusa head column base partially submerged in water
- Arched brick ceilings with Byzantine-era architectural details

LIGHTING & ATMOSPHERE:
- Warm amber spotlights creating pools of golden light on the columns
- Dramatic shadows between the columns adding mystery and depth
- Reflections dancing on the water surface
- Cool stone tones contrasted with warm artificial lighting

CLOTHING:
The child is wearing {clothing_description}.

COMPOSITION REQUIREMENTS:
- Child positioned in lower third of the image
- Upper 30% shows the grand ceiling and columns creating sense of scale and open space for title text
- Columns framing the child from both sides

No text, no letters, no words in the image."""


GOBEKLITEPE_COVER = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing in awe before the ancient megalithic T-shaped pillars of Göbeklitepe, the world's oldest known temple, in southeastern Turkey.

ICONIC BACKGROUND ELEMENTS (must include):
- Massive T-shaped limestone pillars (3-5 meters tall) with intricate animal carvings — foxes, lions, snakes etched into stone
- Circular stone enclosures with concentric rings of pillars partially excavated from the earth
- The vast Harran Plain stretching to the horizon under a dramatic sky
- Rolling golden-brown hills of the Şanlıurfa steppe landscape

LIGHTING & ATMOSPHERE:
- Magical golden hour light casting dramatic shadows from the towering pillars
- Warm amber and honey tones across the ancient limestone
- Sense of deep mystery and ancient wonder — 12,000 years of history
- Warm earth tones: golden sandstone, dusty amber, sage green, sky blue

CLOTHING:
The child is wearing {clothing_description}.

COMPOSITION REQUIREMENTS:
- Child positioned in lower third of the image
- Upper 30% shows the dramatic sky and pillar tops, open space for title text overlay
- T-shaped pillars framing the child from both sides
- Sense of ancient mystery and archaeological wonder

No text, no letters, no words in the image."""


EFES_COVER = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing in wonder before the magnificent Library of Celsus in the ancient city of Ephesus, on the Aegean coast of Turkey.

ICONIC BACKGROUND ELEMENTS (must include):
- The grand two-story facade of the Library of Celsus with ornate Corinthian columns and carved statues in niches
- Marble-paved Curetes Street stretching behind with ancient column ruins on both sides
- Scattered ancient marble columns and capitals with intricate carvings
- Lush Mediterranean vegetation — cypress trees, olive groves, wild poppies between stones

LIGHTING & ATMOSPHERE:
- Warm golden Mediterranean light casting dramatic shadows through ancient columns
- The white marble glowing warmly in golden sunlight
- Sense of grandeur, ancient civilization, and archaeological wonder
- Color palette: warm marble white, golden honey, Mediterranean blue sky, olive green

CLOTHING:
The child is wearing {clothing_description}.

COMPOSITION REQUIREMENTS:
- Child positioned in lower third of the image
- Upper 30% shows blue Mediterranean sky and column tops, open space for title text overlay
- Celsus Library columns framing the child from both sides
- Sense of ancient grandeur and wonder

No text, no letters, no words in the image."""


CATALHOYUK_COVER = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing on one of the ancient rooftops of Çatalhöyük, the world's earliest known city, on the vast Konya Plain in central Anatolia, Turkey.

ICONIC BACKGROUND ELEMENTS (must include):
- Dense cluster of ancient mud-brick houses built wall-to-wall with no streets — a rooftop cityscape
- Wooden ladders poking up from roof openings — the only way to enter houses through the ceiling
- The vast flat Çumra Plain stretching to distant Taurus Mountains on the horizon
- Ancient wall paintings visible through roof openings — hunting scenes with bulls and deer

LIGHTING & ATMOSPHERE:
- Warm golden hour light casting shadows across the flat rooftop landscape
- Earthy color palette: warm ochre, terracotta, dusty beige, golden straw, deep brown
- Sense of ancient wonder — 9,000 years of history, the dawn of civilization
- A feeling of communal warmth — humanity's first true neighborhood

CLOTHING:
The child is wearing {clothing_description}.

COMPOSITION REQUIREMENTS:
- Child positioned in lower third of the image
- Upper 30% shows the vast Anatolian sky, open space for title text overlay
- Ladders and roof openings framing the scene
- Sense of Neolithic wonder and archaeological discovery

No text, no letters, no words in the image."""


SUMELA_COVER = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing on the ancient stone terrace of Sümela Monastery, dramatically carved into the sheer cliff face of Karadağ mountain at 1,200 meters altitude in the Altındere Valley near Trabzon, Turkey.

ICONIC BACKGROUND ELEMENTS (must include):
- The monastery's multi-story stone facade built directly into the vertical rock face with arched windows and balconies
- Dense emerald-green Black Sea temperate rainforest covering the steep valley below, shrouded in mist
- A dramatic waterfall cascading down the cliff beside the monastery
- Wisps of mountain fog drifting through the valley between towering spruce trees

LIGHTING & ATMOSPHERE:
- Mystical diffused light filtering through mountain fog and forest canopy
- Deep greens of the Black Sea forests contrasting with warm grey-brown ancient stone
- A sense of hidden wonder — a secret place carved into the mountain
- Color palette: emerald green, misty grey, warm stone beige, Byzantine gold accents

CLOTHING:
The child is wearing {clothing_description}.

COMPOSITION REQUIREMENTS:
- Child positioned in lower third of the image
- Upper 30% shows the cliff face and misty sky, open space for title text overlay
- Vertical cliff and monastery facade framing the scene with dramatic height
- Sense of mystical discovery and mountain wonder

No text, no letters, no words in the image."""


SULTANAHMET_COVER = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing in awe in the grand courtyard of the Sultanahmet Mosque (Blue Mosque) in Istanbul, Turkey, gazing up at the cascade of domes and six minarets.

ICONIC BACKGROUND ELEMENTS (must include):
- The Blue Mosque's majestic cascade of domes — central dome flanked by semi-domes creating a pyramidal silhouette
- Six elegant pencil-shaped minarets soaring into the sky
- The arcaded courtyard with domed portico and central fountain
- Warm Marmara limestone and marble exterior glowing in golden light

LIGHTING & ATMOSPHERE:
- Warm golden hour light bathing domes and minarets in amber glow
- Warm cream-white stone contrasting with deep blue sky
- A feeling of grandeur, serenity, and 400 years of history
- Color palette: warm cream stone, İznik cobalt blue, golden amber, minaret white

CLOTHING:
The child is wearing {clothing_description}.

COMPOSITION REQUIREMENTS:
- Child positioned in lower third of the image
- Upper 30% shows the dome cascade and sky, open space for title text overlay
- Minarets and dome silhouette framing the scene
- Sense of Ottoman architectural grandeur and wonder

No text, no letters, no words in the image."""


TACMAHAL_COVER = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing on the long reflecting pool pathway of the Charbagh gardens, gazing in wonder at the magnificent Taj Mahal rising before them in Agra, India.

ICONIC BACKGROUND ELEMENTS (must include):
- The Taj Mahal's iconic white marble dome and four slender minarets rising against a dramatic sky
- The grand central onion dome (~73 meters tall) flanked by four smaller chattri domes
- The long reflecting pool creating a perfect mirror reflection of the monument
- Symmetrical Charbagh Mughal gardens with manicured lawns, cypress trees, and flowering beds

LIGHTING & ATMOSPHERE:
- Magical golden sunrise or sunset light making the white marble glow with warm pink-gold tones
- Perfect mirror reflection of the Taj in the still reflecting pool water
- Color palette: luminous white marble, warm pink-gold sky, emerald garden green, reflecting pool silver-blue

CLOTHING:
The child is wearing {clothing_description}.

COMPOSITION REQUIREMENTS:
- Child positioned in lower third of the image
- Upper 30% shows the grand dome and minarets, open space for title text overlay
- The Taj Mahal centered and majestic, filling the upper portion
- Perfect symmetry emphasized by the reflecting pool mirror image

No text, no letters, no words in the image."""


ABUSIMBEL_COVER = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing in awe at the base of the colossal facade of the Great Temple of Abu Simbel in southern Egypt, dwarfed by the four enormous seated statues of Pharaoh Ramesses II carved directly into the cliff face.

ICONIC BACKGROUND ELEMENTS (must include):
- The four colossal seated statues of Ramesses II (~20 meters tall each) carved into golden sandstone cliff — serene pharaonic faces with double crowns
- The temple entrance between the two central statues — a dark doorway leading into the mountain
- Hieroglyphic carvings and cartouches covering the facade
- The golden Nubian desert and Lake Nasser's blue waters visible in the distance
- A brilliant Egyptian sun casting dramatic shadows

LIGHTING & ATMOSPHERE:
- Intense golden Egyptian sunlight illuminating the sandstone facade in warm amber-gold tones
- Deep dramatic shadows cast by the colossal statues creating a sense of immense scale
- A vast cloudless deep blue Egyptian sky contrasting with the golden stone
- Color palette: pharaonic gold sandstone, deep Nile blue, desert amber, sky azure

CLOTHING:
The child is wearing {clothing_description}.

COMPOSITION REQUIREMENTS:
- Child positioned in lower third of the image
- Upper 30% shows dramatic sky and statue tops, open space for title text overlay
- The four colossal Ramesses statues filling the frame with monumental grandeur
- Sense of ancient power, mystery, and archaeological wonder

No text, no letters, no words in the image."""


KUDUS_COVER = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing on the ancient stone ramparts of the Old City walls (built by Suleiman the Magnificent in the 16th century), gazing out over the golden-stone rooftops and domes of the walled Old City of Jerusalem.

ICONIC BACKGROUND ELEMENTS (must include):
- The magnificent Ottoman-era city walls and crenellated battlements — warm golden limestone (Jerusalem stone)
- A panorama of the Old City rooftops: golden-stone domes, arches, and flat rooftops densely packed within the walls
- The iconic golden Dome of the Rock catching the sunlight — the most recognizable architectural landmark
- Ancient stone gates with massive arched doorways
- Olive trees and cypress trees dotting the hillsides beyond the walls

LIGHTING & ATMOSPHERE:
- Warm golden hour light bathing the Jerusalem stone in its famous honeyed glow
- Every surface glowing gold — the unique luminosity Jerusalem stone is famous for
- A vast Mediterranean blue sky with wispy clouds
- Color palette: Jerusalem gold stone, Mediterranean blue, olive green, warm amber, dome gold

CLOTHING:
The child is wearing {clothing_description}.

COMPOSITION REQUIREMENTS:
- Child positioned in lower third of the image
- Upper 30% shows the golden domes and sky, open space for title text overlay
- Ancient walls and architecture framing the scene
- Sense of ancient multicultural wonder and timeless beauty

No text, no letters, no words in the image."""


GALATA_COVER = """A breathtaking children's book cover illustration.

SCENE COMPOSITION:
A young child {scene_description}, standing on the famous 360-degree observation balcony of the Galata Tower in Istanbul, Turkey, with the wind in their clothes and the entire city spread out below.

ICONIC BACKGROUND ELEMENTS (must include):
- The Galata Tower's distinctive cylindrical stone body and conical cap roof visible below the balcony railing — warm grey Genoese stone, Gothic architectural details
- A sweeping 360° panorama of Istanbul: the Golden Horn (Haliç) sparkling below, the Bosphorus strait with ferries, the Historic Peninsula skyline
- The Galata Bridge spanning the Golden Horn with tiny fishermen silhouettes, colorful ferry boats
- Rooftops of Beyoğlu/Karaköy cascading down the hillside — terracotta and grey tile roofs, pastel Ottoman-era buildings
- Flocks of seagulls soaring at eye level around the tower

LIGHTING & ATMOSPHERE:
- Magical golden hour sunset light painting the city in warm amber and rose tones
- The Bosphorus and Golden Horn reflecting sunset colors like liquid gold
- A vast dramatic sky with scattered clouds lit in orange, pink, and purple
- Color palette: warm stone grey, golden amber, Bosphorus blue-green, sunset rose, terracotta rooftops

CLOTHING:
The child is wearing {clothing_description}.

COMPOSITION REQUIREMENTS:
- Child positioned in lower third of the image
- Upper 30% shows the conical tower cap and sky, open space for title text overlay
- Epic cinematic scale showing the vastness of Istanbul from the tower's vantage point
- Seagulls and conical cap framing the upper portion

No text, no letters, no words in the image."""


async def main():
    async with async_session_factory() as db:
        # Update Kapadokya
        r1 = await db.execute(
            text("UPDATE scenarios SET cover_prompt_template = :tpl WHERE name LIKE :name"),
            {"tpl": KAPADOKYA_COVER, "name": "%Kapadokya%"},
        )
        print(f"Kapadokya updated: {r1.rowcount} rows")

        # Update Yerebatan
        r2 = await db.execute(
            text("UPDATE scenarios SET cover_prompt_template = :tpl WHERE name LIKE :name"),
            {"tpl": YEREBATAN_COVER, "name": "%Yerebatan%"},
        )
        print(f"Yerebatan updated: {r2.rowcount} rows")

        # Update Göbeklitepe
        r3 = await db.execute(
            text("UPDATE scenarios SET cover_prompt_template = :tpl WHERE name LIKE :name"),
            {"tpl": GOBEKLITEPE_COVER, "name": "%Göbeklitepe%"},
        )
        print(f"Göbeklitepe updated: {r3.rowcount} rows")

        # Update Efes
        r4 = await db.execute(
            text("UPDATE scenarios SET cover_prompt_template = :tpl WHERE name LIKE :name"),
            {"tpl": EFES_COVER, "name": "%Efes%"},
        )
        print(f"Efes updated: {r4.rowcount} rows")

        # Update Çatalhöyük
        r5 = await db.execute(
            text("UPDATE scenarios SET cover_prompt_template = :tpl WHERE name LIKE :name"),
            {"tpl": CATALHOYUK_COVER, "name": "%Çatalhöyük%"},
        )
        print(f"Çatalhöyük updated: {r5.rowcount} rows")

        # Update Sümela
        r6 = await db.execute(
            text("UPDATE scenarios SET cover_prompt_template = :tpl WHERE name LIKE :name"),
            {"tpl": SUMELA_COVER, "name": "%Sümela%"},
        )
        print(f"Sümela updated: {r6.rowcount} rows")

        # Update Sultanahmet
        r7 = await db.execute(
            text("UPDATE scenarios SET cover_prompt_template = :tpl WHERE name LIKE :name"),
            {"tpl": SULTANAHMET_COVER, "name": "%Sultanahmet%"},
        )
        print(f"Sultanahmet updated: {r7.rowcount} rows")

        # Update Galata
        r8 = await db.execute(
            text("UPDATE scenarios SET cover_prompt_template = :tpl WHERE name LIKE :name"),
            {"tpl": GALATA_COVER, "name": "%Galata%"},
        )
        print(f"Galata updated: {r8.rowcount} rows")

        # Update Kudüs
        r9 = await db.execute(
            text("UPDATE scenarios SET cover_prompt_template = :tpl WHERE name LIKE :name"),
            {"tpl": KUDUS_COVER, "name": "%Kudüs%"},
        )
        print(f"Kudüs updated: {r9.rowcount} rows")

        # Update Abu Simbel
        r10 = await db.execute(
            text("UPDATE scenarios SET cover_prompt_template = :tpl WHERE name LIKE :name"),
            {"tpl": ABUSIMBEL_COVER, "name": "%Abu Simbel%"},
        )
        print(f"Abu Simbel updated: {r10.rowcount} rows")

        # Update Tac Mahal
        r11 = await db.execute(
            text("UPDATE scenarios SET cover_prompt_template = :tpl WHERE name LIKE :name"),
            {"tpl": TACMAHAL_COVER, "name": "%Tac Mahal%"},
        )
        print(f"Tac Mahal updated: {r11.rowcount} rows")

        await db.commit()
        print("Done!")


asyncio.run(main())
