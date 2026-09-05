"""Accurate, multi-domain offline knowledge database for informative explainer videos.

Each topic includes:
- domain: "astronomy", "earth_science", "technology", "biology"
- title: clear, engaging title
- subtitle: domain context
- hook: opening sentence
- metrics: key factual numbers/units for callout cards
- schematic_type: "orbital_system", "layer_stack", "network_lattice", "quantum_field", "spec_blueprint"
- segments: 4-phase structured timeline:
    1. Overview & Hook
    2. Anatomy & Mechanism
    3. Mind-Blowing Scientific Data
    4. Significance & Future Horizon
"""

from __future__ import annotations

from typing import Any
import numpy as np

# Structured knowledge domains
KNOWLEDGE_TOPICS: list[dict[str, Any]] = [
    # --- ASTRONOMY & COSMOS ---
    {
        "id": "james_webb_telescope",
        "domain": "astronomy",
        "domain_label": "ASTROPHYSICS & DEEP SPACE",
        "title": "The James Webb Space Telescope",
        "subtitle": "Unfolding the Cosmic Dawn",
        "hook": "Positioned 1.5 million kilometers away, humanity's premier eye gazes into the first galaxies of creation.",
        "schematic_type": "orbital_system",
        "metrics": [
            {"label": "Orbit Distance", "val": "1.5M", "unit": "km (L2 Point)"},
            {"label": "Primary Mirror", "val": "6.5", "unit": "meters wide"},
            {"label": "Operating Temp", "val": "-233", "unit": "Celsius (-388°F)"},
            {"label": "Cosmic Reach", "val": "13.6B", "unit": "years back"},
        ],
        "segments": [
            {
                "phase": "OVERVIEW",
                "headline": "Orbiting the Second Lagrange Point",
                "body": "Webb orbits the Sun-Earth L2 gravitational balance point, staying in perpetual shadow from Earth and the Moon.",
                "data_point": "1.5 million km from Earth",
                "voice_line": "Positioned at the second Lagrange point, the James Webb Space Telescope maintains a gravitationally stable orbit one and a half million kilometers from Earth.",
            },
            {
                "phase": "MECHANISM",
                "headline": "18 Beryllium Hexagonal Mirrors",
                "body": "Gold-coated mirrors act as a single light collector, capturing faint infrared photons emitted over 13.5 billion years ago.",
                "data_point": "100-nanometer gold coating",
                "voice_line": "Its primary mirror comprises eighteen gold-plated beryllium segments that focus faint infrared light stretched across billions of light-years.",
            },
            {
                "phase": "SCIENTIFIC DATA",
                "headline": "Sub-Kelvin Thermal Shielding",
                "body": "A five-layer Kapton sunshield keeps instruments chilled to 40 Kelvin, preventing thermal radiation from masking cosmic signals.",
                "data_point": "Sunshield: SPF 1,000,000",
                "voice_line": "A five-layer tennis-court-sized sunshield drops temperatures by three hundred degrees, shielding sensitive detectors from solar glare.",
            },
            {
                "phase": "HORIZON",
                "headline": "Decoding Exoplanet Atmospheres",
                "body": "By analyzing starlight filtering through alien atmospheres, Webb searches for signatures of water vapor, methane, and carbon dioxide.",
                "data_point": "Hundreds of exoplanets surveyed",
                "voice_line": "By dissecting light passing through exoplanet atmospheres, Webb is actively searching for the chemical fingerprints of alien worlds.",
            },
        ],
    },
    {
        "id": "supermassive_black_holes",
        "domain": "astronomy",
        "domain_label": "GENERAL RELATIVITY & GRAVITATION",
        "title": "Supermassive Black Holes",
        "subtitle": "Cosmic Titans and Event Horizons",
        "hook": "Regions where gravity is so intense that not even light can achieve escape velocity.",
        "schematic_type": "orbital_system",
        "metrics": [
            {"label": "Event Horizon", "val": "24M", "unit": "km radius (Sgr A*)"},
            {"label": "Core Mass", "val": "4.3M", "unit": "Solar Masses"},
            {"label": "Escape Speed", "val": "> c", "unit": "Exceeds Light"},
            {"label": "Accretion Temp", "val": "10M", "unit": "Kelvin (X-rays)"},
        ],
        "segments": [
            {
                "phase": "OVERVIEW",
                "headline": "The Boundary of No Return",
                "body": "At the event horizon, the escape velocity equals the speed of light. Any matter crossing this boundary is irrevocably pulled into the singularity.",
                "data_point": "Universal speed limit reached",
                "voice_line": "At the event horizon of a black hole, the gravitational pull becomes so immense that escape velocity surpasses the speed of light itself.",
            },
            {
                "phase": "MECHANISM",
                "headline": "Superheated Accretion Disks",
                "body": "Gas and stellar remnants swirl toward the event horizon at relativistic speeds, heating up to millions of degrees through friction.",
                "data_point": "Plasma moving at 0.3c",
                "voice_line": "Infalling matter forms a raging accretion disk, spiraling at near-light speeds and emitting high-energy X-ray radiation visible across the cosmos.",
            },
            {
                "phase": "SCIENTIFIC DATA",
                "headline": "Extreme Gravitational Time Dilation",
                "body": "As predicted by Einstein's equations, time slows down drastically for an outside observer watching an object approach the horizon.",
                "data_point": "Infinite red-shift at r = 2GM/c²",
                "voice_line": "According to general relativity, extreme spacetime curvature causes time to slow down dramatically near the Schwarzschild radius.",
            },
            {
                "phase": "HORIZON",
                "headline": "Anchors of Galactic Evolution",
                "body": "Supermassive black holes reside at the core of nearly every major galaxy, regulating stellar birth through immense plasma jets.",
                "data_point": "Relativistic jets > 10,000 ly",
                "voice_line": "These gravitational anchors dictate the architecture of host galaxies, launching relativistic jets that shape star formation across thousands of light-years.",
            },
        ],
    },
    {
        "id": "neutron_stars_pulsars",
        "domain": "astronomy",
        "domain_label": "EXTREME STELLAR PHYSICS",
        "title": "Neutron Stars & Pulsars",
        "subtitle": "The Densest Matter in the Universe",
        "hook": "A single teaspoon of neutron star matter would weigh roughly six billion tons on Earth.",
        "schematic_type": "orbital_system",
        "metrics": [
            {"label": "Diameter", "val": "20", "unit": "km (City-sized)"},
            {"label": "Density", "val": "10^17", "unit": "kg/m³"},
            {"label": "Spin Rate", "val": "716", "unit": "rotations/sec"},
            {"label": "Magnetic Field", "val": "10^12", "unit": "Gauss"},
        ],
        "segments": [
            {
                "phase": "OVERVIEW",
                "headline": "Collapse of a Massive Star",
                "body": "When a star 10 to 25 times more massive than our Sun undergoes a supernova, its core collapses under catastrophic gravity.",
                "data_point": "Protons and electrons fuse into neutrons",
                "voice_line": "When a giant star explodes in a supernova, its iron core collapses violently, fusing protons and electrons into pure nuclear matter.",
            },
            {
                "phase": "MECHANISM",
                "headline": "Lighthouse Beams of Radiation",
                "body": "Magnetic fields accelerate charged particles, shooting twin relativistic beams of radio waves into the void.",
                "data_point": "Precision clocks of the universe",
                "voice_line": "Channeling extreme magnetic energy, pulsars cast twin beams of electromagnetic radiation across space like cosmic lighthouses.",
            },
            {
                "phase": "SCIENTIFIC DATA",
                "headline": "Millisecond Rotations",
                "body": "Conservation of angular momentum causes these 20-kilometer spheres to spin hundreds of times every single second.",
                "data_point": "Surface velocity reaches 24% speed of light",
                "voice_line": "Spinning hundreds of times per second, their outer crusts travel at a significant fraction of the speed of light.",
            },
            {
                "phase": "HORIZON",
                "headline": "Kilonovae & The Origin of Gold",
                "body": "When binary neutron stars collide, the extreme neutron-rich environment synthesizes heavy elements like gold and platinum.",
                "data_point": "Primary forge of heavy elements",
                "voice_line": "Collisions between neutron stars forge the universe's heaviest precious metals, including the gold and platinum found on Earth.",
            },
        ],
    },

    # --- EARTH & OCEAN SCIENCES ---
    {
        "id": "mariana_trench",
        "domain": "earth_science",
        "domain_label": "OCEANOGRAPHY & HADAL ZONE",
        "title": "The Mariana Trench & Challenger Deep",
        "subtitle": "Earth's Deepest Frontier",
        "hook": "Nearly eleven kilometers below the ocean surface lies a dark realm under crushing hydrostatic pressure.",
        "schematic_type": "layer_stack",
        "metrics": [
            {"label": "Maximum Depth", "val": "10,994", "unit": "meters (Challenger Deep)"},
            {"label": "Water Pressure", "val": "1,086", "unit": "bar (1,000x surface)"},
            {"label": "Water Temp", "val": "1 - 4", "unit": "degrees Celsius"},
            {"label": "Trench Length", "val": "2,550", "unit": "kilometers"},
        ],
        "segments": [
            {
                "phase": "OVERVIEW",
                "headline": "Descending Through the Oceanic Zones",
                "body": "From the sunlit Epipelagic zone to the pitch-black Hadal zone, water pressure multiplies exponentially.",
                "data_point": "Sunlight vanishes completely at 1,000m",
                "voice_line": "Descending nearly eleven kilometers into the western Pacific, the Mariana Trench plunges into the pitch-black Hadal zone.",
            },
            {
                "phase": "MECHANISM",
                "headline": "Subduction Zone Tectonics",
                "body": "Formed where the dense Pacific Plate dives beneath the smaller Mariana Plate, dragging the seabed downward.",
                "data_point": "Convergence rate: 35 mm per year",
                "voice_line": "This colossal chasm is formed by subduction, where the ancient Pacific tectonic plate dives beneath the Mariana plate.",
            },
            {
                "phase": "SCIENTIFIC DATA",
                "headline": "Hydrostatic Pressure of 1,000 Atmospheres",
                "body": "At the bottom, pressure equals eight tons per square inch—equivalent to balancing an elephant on your thumb.",
                "data_point": "108 megapascals at seabed",
                "voice_line": "At the floor of Challenger Deep, hydrostatic pressure exceeds one thousand atmospheres, demanding titanium-hulled submersibles.",
            },
            {
                "phase": "HORIZON",
                "headline": "Bioluminescence & Extremophile Life",
                "body": "Organisms here survive without sunlight, relying on piezolyte cellular stabilizers and chemosynthetic food webs.",
                "data_point": "Xenophyophores and amphipods",
                "voice_line": "Despite the crushing abyss, specialized extremophiles thrive by utilizing chemosynthesis and cellular pressure adaptations.",
            },
        ],
    },
    {
        "id": "aurora_borealis",
        "domain": "earth_science",
        "domain_label": "GEOMAGNETIC & ATMOSPHERIC SCIENCE",
        "title": "Aurora Borealis & The Magnetosphere",
        "subtitle": "The Earth's Cosmic Shield in Motion",
        "hook": "Glowing curtains of light reveal our planet's magnetic shield deflecting high-energy solar storms.",
        "schematic_type": "layer_stack",
        "metrics": [
            {"label": "Altitude Range", "val": "100 - 400", "unit": "km (Thermosphere)"},
            {"label": "Solar Wind Speed", "val": "400 - 800", "unit": "km / second"},
            {"label": "Green Light Wave", "val": "557.7", "unit": "nm (Atomic Oxygen)"},
            {"label": "Red Light Wave", "val": "630.0", "unit": "nm (High-altitude O)"},
        ],
        "segments": [
            {
                "phase": "OVERVIEW",
                "headline": "Solar Wind Collisions in the Night Sky",
                "body": "Streams of plasma ejected by the Sun travel across 150 million kilometers, colliding with Earth's magnetosphere.",
                "data_point": "Plasma transit time: 2 to 4 days",
                "voice_line": "Charged solar winds streaming from coronal mass ejections strike Earth's magnetic field at hundreds of kilometers per second.",
            },
            {
                "phase": "MECHANISM",
                "headline": "Funneling Toward the Polar Cusps",
                "body": "Magnetic field lines channel incoming electrons and protons down into polar upper atmospheric layers.",
                "data_point": "Magnetic reconnection in magnetotail",
                "voice_line": "Earth's magnetic geometry funnels these energetic particles into the polar cusps, where they collide with atmospheric gases.",
            },
            {
                "phase": "SCIENTIFIC DATA",
                "headline": "Atomic Excitation and Color Spectrum",
                "body": "Colliding electrons excite oxygen and nitrogen atoms; returning to ground state releases characteristic spectral wavelengths.",
                "data_point": "Green at 100km, violet at 80km",
                "voice_line": "Excited oxygen atoms emit vibrant green wavelengths at one hundred kilometers, while nitrogen creates crimson and violet borders.",
            },
            {
                "phase": "HORIZON",
                "headline": "Protecting the Biosphere",
                "body": "Without this dynamic geomagnetic deflection, cosmic radiation would strip our atmosphere and sterilize the surface.",
                "data_point": "Critical shield for planetary habitability",
                "voice_line": "This awe-inspiring light show is visual proof of Earth's geomagnetic shield protecting our biosphere from lethal cosmic rays.",
            },
        ],
    },
    {
        "id": "earth_atmospheric_layers",
        "domain": "earth_science",
        "domain_label": "METEOROLOGY & ATMOSPHERIC PHYSICS",
        "title": "Layers of the Atmosphere",
        "subtitle": "The Thermal Architecture of Sky and Space",
        "hook": "A delicate envelope of gases spanning five distinct thermal layers preserves all terrestrial life.",
        "schematic_type": "layer_stack",
        "metrics": [
            {"label": "Troposphere", "val": "0 - 12", "unit": "km (All Weather)"},
            {"label": "Ozone Peak", "val": "20 - 30", "unit": "km (UV Absorption)"},
            {"label": "Mesosphere Min", "val": "-90", "unit": "Celsius (Coldest)"},
            {"label": "Kármán Line", "val": "100", "unit": "km (Edge of Space)"},
        ],
        "segments": [
            {
                "phase": "OVERVIEW",
                "headline": "The Troposphere: Cradle of Weather",
                "body": "Holding 75% of atmospheric mass and nearly all water vapor, convection here powers clouds, rain, and winds.",
                "data_point": "Average lapse rate: 6.5°C per km",
                "voice_line": "The troposphere contains seventy-five percent of our air and nearly all water vapor, generating all weather on Earth.",
            },
            {
                "phase": "MECHANISM",
                "headline": "Stratosphere and the Ozone Shield",
                "body": "Temperature increases with altitude here because the triatomic ozone layer absorbs harmful solar ultraviolet-B radiation.",
                "data_point": "Absorption of UV rays (200-310 nm)",
                "voice_line": "Above it, the stratosphere warms with height as its vital ozone layer absorbs high-energy ultraviolet radiation from the sun.",
            },
            {
                "phase": "SCIENTIFIC DATA",
                "headline": "Mesosphere: Meteor Vaporization Zone",
                "body": "The coldest atmospheric realm, with temperatures plunging to minus 90 degrees Celsius, vaporizing meteors via compression friction.",
                "data_point": "Meteors disintegrate at 80 km",
                "voice_line": "In the freezing mesosphere, plummeting meteors burn up through intense atmospheric compression and friction.",
            },
            {
                "phase": "HORIZON",
                "headline": "The Thermosphere & Exosphere",
                "body": "Extending into the vacuum of space, home to the International Space Station and the transition to interplanetary void.",
                "data_point": "Kármán line at 100 km boundary",
                "voice_line": "Finally, the thermosphere and exosphere merge into the orbital realm, where satellites orbit Earth in the quiet of near-vacuum.",
            },
        ],
    },

    # --- TECHNOLOGY, PHYSICS & COMPUTING ---
    {
        "id": "quantum_computing",
        "domain": "technology",
        "domain_label": "QUANTUM INFORMATION SCIENCE",
        "title": "Quantum Computing & Superposition",
        "subtitle": "Processing Beyond Classical Limits",
        "hook": "Harnessing the bizarre laws of quantum mechanics to compute across exponential states simultaneously.",
        "schematic_type": "quantum_field",
        "metrics": [
            {"label": "State Space", "val": "2^N", "unit": "Simultaneous States"},
            {"label": "Operating Temp", "val": "15", "unit": "milliKelvin (Colder than Space)"},
            {"label": "Qubit Fidelity", "val": "99.9", "unit": "% Gate Precision"},
            {"label": "Coherence Time", "val": "100+", "unit": "Microseconds"},
        ],
        "segments": [
            {
                "phase": "OVERVIEW",
                "headline": "Beyond Binary Bits: The Qubit",
                "body": "While classical bits are strictly 0 or 1, a qubit exists as a continuous probability vector in a complex Hilbert space.",
                "data_point": "Bloch sphere representation: |psi> = a|0> + b|1>",
                "voice_line": "Unlike classical bits bound to zero or one, quantum qubits exploit superposition to represent both states simultaneously.",
            },
            {
                "phase": "MECHANISM",
                "headline": "Entanglement and Quantum Gates",
                "body": "Entangling multiple qubits creates correlated states where the properties of one instantaneously determine another.",
                "data_point": "Non-local correlation across qubits",
                "voice_line": "Through quantum entanglement, multiple qubits link together, unlocking computational power that scales exponentially with each added qubit.",
            },
            {
                "phase": "SCIENTIFIC DATA",
                "headline": "Dilution Refrigerators Near Absolute Zero",
                "body": "Superconducting qubits must be shielded from thermal vibration at 15 milliKelvin—hundreds of times colder than interstellar space.",
                "data_point": "0.015 Kelvin above absolute zero",
                "voice_line": "Operating inside multi-stage dilution refrigerators, quantum processors are kept colder than outer space to preserve fragile quantum coherence.",
            },
            {
                "phase": "HORIZON",
                "headline": "Revolutionizing Chemistry and Cryptography",
                "body": "Quantum algorithms like Shor's and Grover's promise to simulate molecular folding, design new superconductors, and transform security.",
                "data_point": "Exponential speedup for prime factorization",
                "voice_line": "These machines will revolutionize molecular simulation, clean energy catalysis, and advanced cryptographic systems.",
            },
        ],
    },
    {
        "id": "semiconductor_lithography",
        "domain": "technology",
        "domain_label": "NANOTECHNOLOGY & MICROELECTRONICS",
        "title": "Silicon Lithography & The Microchip",
        "subtitle": "Carving Billions of Transistors with Light",
        "hook": "Modern processors pack over one hundred billion switches into an area smaller than a postage stamp.",
        "schematic_type": "spec_blueprint",
        "metrics": [
            {"label": "Transistor Scale", "val": "2 - 3", "unit": "Nanometers (20 atoms wide)"},
            {"label": "EUV Wavelength", "val": "13.5", "unit": "Nanometers"},
            {"label": "Gate Count", "val": "100B+", "unit": "Transistors per Die"},
            {"label": "Laser Pulse Freq", "val": "50,000", "unit": "Pulses / Second"},
        ],
        "segments": [
            {
                "phase": "OVERVIEW",
                "headline": "Extreme Ultraviolet Lithography",
                "body": "To etch features narrower than a virus, lithography machines vaporize molten tin droplets with high-power CO2 lasers.",
                "data_point": "Molten tin fired at 70 meters per second",
                "voice_line": "Extreme ultraviolet lithography uses pulsed lasers firing at fifty thousand times per second to vaporize molten tin and generate extreme ultraviolet light.",
            },
            {
                "phase": "MECHANISM",
                "headline": "Sub-Nanometer Optical Mirrors",
                "body": "Because EUV light is absorbed by air and glass, reflection occurs across mirrors polished to single-atom smoothness.",
                "data_point": "Molybdenum-silicon multilayer mirrors",
                "voice_line": "Because air absorbs this extreme light, beams travel in pure vacuum, bouncing across mirrors polished to sub-atomic precision.",
            },
            {
                "phase": "SCIENTIFIC DATA",
                "headline": "Trillions of Calculations per Second",
                "body": "Modern FinFET and Gate-All-Around (GAA) architectures control quantum tunneling across gates only a few atoms thick.",
                "data_point": "Current leakage controlled at quantum scale",
                "voice_line": "Nanoscale transistors operate at the threshold of quantum mechanics, shuttling billions of electrons with pico-second switching times.",
            },
            {
                "phase": "HORIZON",
                "headline": "The Engine of Modern Civilization",
                "body": "From supercomputers and smartphones to autonomous vehicles and neural networks, modern society runs on etched silicon.",
                "data_point": "Foundation of all modern computing",
                "voice_line": "These sub-microscopic circuits form the computational engine of our world, powering modern computing and artificial intelligence.",
            },
        ],
    },
    {
        "id": "neural_networks_ai",
        "domain": "technology",
        "domain_label": "ARTIFICIAL INTELLIGENCE & COMPUTER SCIENCE",
        "title": "Neural Networks & Artificial Intelligence",
        "subtitle": "Mathematical Architectures of Machine Learning",
        "hook": "Billions of matrix multiplications converge to recognize patterns, translate language, and simulate human cognition.",
        "schematic_type": "network_lattice",
        "metrics": [
            {"label": "Parameter Scale", "val": "100B+", "unit": "Synaptic Weights"},
            {"label": "Attention Matrix", "val": "Q * K^T", "unit": "Scaled Dot-Product"},
            {"label": "Compute Power", "val": "10^24", "unit": "FLOPS Training Run"},
            {"label": "Layer Depth", "val": "96+", "unit": "Transformer Blocks"},
        ],
        "segments": [
            {
                "phase": "OVERVIEW",
                "headline": "From Biological Inspiration to Tensor Math",
                "body": "Artificial neurons receive inputs, compute weighted sums, add biases, and pass results through non-linear activation functions.",
                "data_point": "y = activation(W * x + b)",
                "voice_line": "Artificial neural networks structure information through layers of interconnected mathematical nodes inspired by biological synapses.",
            },
            {
                "phase": "MECHANISM",
                "headline": "Backpropagation and Gradient Descent",
                "body": "Errors calculated at the output layer propagate backward using the chain rule of calculus, adjusting weights to minimize loss.",
                "data_point": "Minimizing loss surface in high dimensions",
                "voice_line": "Using the chain rule of calculus, backpropagation computes error gradients, nudging billions of parameters closer to mathematical precision.",
            },
            {
                "phase": "SCIENTIFIC DATA",
                "headline": "Transformer Self-Attention Mechanisms",
                "body": "Self-attention calculates pairwise relationships between every token in a sequence, capturing deep contextual dependencies.",
                "data_point": "Parallel processing across full context window",
                "voice_line": "Modern transformer architectures leverage self-attention, dynamically tracking contextual relationships across vast arrays of data simultaneously.",
            },
            {
                "phase": "HORIZON",
                "headline": "Accelerating Scientific Discovery",
                "body": "AI models now predict 3D protein folding, simulate plasma fusion reactions, and accelerate materials discovery by decades.",
                "data_point": "AlphaFold mapped 200M+ proteins",
                "voice_line": "Today, these neural models are accelerating scientific breakthroughs, decoding protein structures and discovering novel materials.",
            },
        ],
    },

    # --- BIOLOGY & LIFE SCIENCES ---
    {
        "id": "human_brain_synapses",
        "domain": "biology",
        "domain_label": "NEUROSCIENCE & CELL BIOLOGY",
        "title": "The Human Brain & Neural Synapses",
        "subtitle": "The Most Complex Structure in the Known Universe",
        "hook": "Eighty-six billion neurons forming one hundred trillion synaptic connections generate consciousness, thought, and memory.",
        "schematic_type": "network_lattice",
        "metrics": [
            {"label": "Neuron Count", "val": "86B", "unit": "Individual Cells"},
            {"label": "Synapses", "val": "100T", "unit": "Synaptic Links"},
            {"label": "Power Draw", "val": "20", "unit": "Watts (Energy Efficient)"},
            {"label": "Signal Speed", "val": "120", "unit": "m/s (Action Potential)"},
        ],
        "segments": [
            {
                "phase": "OVERVIEW",
                "headline": "The 86-Billion Neuron Network",
                "body": "Each neuron communicates with thousands of neighbors, creating a dense electro-chemical web capable of real-time cognition.",
                "data_point": "1.4 kg organ with 20% of resting oxygen use",
                "voice_line": "The human brain contains eighty-six billion neurons, forming an electro-chemical network of unparalleled complexity.",
            },
            {
                "phase": "MECHANISM",
                "headline": "Electrochemical Action Potentials",
                "body": "Ion channels open to rush sodium and potassium across cell membranes, propagating electrical spikes down the axon.",
                "data_point": "Membrane potential shifts: -70 mV to +30 mV",
                "voice_line": "Sodium and potassium ion channels generate rapid electrical spikes that travel along axons at over one hundred meters per second.",
            },
            {
                "phase": "SCIENTIFIC DATA",
                "headline": "Synaptic Neurotransmitter Release",
                "body": "At the synaptic cleft, calcium influx triggers vesicles to release neurotransmitters like glutamate, GABA, and dopamine.",
                "data_point": "Synaptic gap is just 20 nanometers wide",
                "voice_line": "Across twenty-nanometer synaptic gaps, chemical neurotransmitters transmit signals between neurons in fractions of a millisecond.",
            },
            {
                "phase": "HORIZON",
                "headline": "Synaptic Plasticity & Learning",
                "body": "Connections strengthen or weaken based on activity ('neurons that fire together wire together'), encoding lifelong memory.",
                "data_point": "Long-term potentiation (LTP) mechanisms",
                "voice_line": "Through synaptic plasticity, these connections continuously rewire, physically etching our memories and knowledge into neural architecture.",
            },
        ],
    },
    {
        "id": "dna_double_helix",
        "domain": "biology",
        "domain_label": "MOLECULAR BIOLOGY & GENETICS",
        "title": "The DNA Double Helix & Genetic Code",
        "subtitle": "The Molecular Blueprint of Life",
        "hook": "Three billion base pairs packaged into the nucleus of almost every cell dictate the biochemical symphony of living organisms.",
        "schematic_type": "quantum_field",
        "metrics": [
            {"label": "Base Pairs", "val": "3.2B", "unit": "Human Genome"},
            {"label": "Helix Width", "val": "2.0", "unit": "Nanometers"},
            {"label": "Total Length", "val": "2.0", "unit": "Meters per Cell"},
            {"label": "Copy Error Rate", "val": "1 in 10^9", "unit": "Polymerase Proofreading"},
        ],
        "segments": [
            {
                "phase": "OVERVIEW",
                "headline": "The Four Chemical Letters: A, T, C, G",
                "body": "Adenine pairs strictly with Thymine, and Cytosine with Guanine, held together by complementary hydrogen bonds.",
                "data_point": "Watson-Crick antiparallel double helix",
                "voice_line": "Life's instruction manual is written in four nucleotide bases—adenine, thymine, cytosine, and guanine—paired across a double helix.",
            },
            {
                "phase": "MECHANISM",
                "headline": "Transcription and Translation",
                "body": "RNA polymerase transcribes DNA into messenger RNA, which ribosomes translate into three-dimensional protein machinery.",
                "data_point": "Codon triplet codes for 20 amino acids",
                "voice_line": "Ribosomes read this genetic code in three-letter codons, assembling strings of amino acids into the proteins that build our bodies.",
            },
            {
                "phase": "SCIENTIFIC DATA",
                "headline": "Extreme Chromatin Compaction",
                "body": "Two meters of linear DNA are wound around histone protein spools, condensed into microscopic chromosomes inside a 6-micron nucleus.",
                "data_point": "10,000-fold compaction factor",
                "voice_line": "Two meters of molecular DNA are wrapped around histone proteins, fitting effortlessly inside a cell nucleus six microns wide.",
            },
            {
                "phase": "HORIZON",
                "headline": "CRISPR and Genomic Engineering",
                "body": "Molecular scissors adapted from bacterial immune systems now enable precise single-base editing to treat genetic diseases.",
                "data_point": "Cas9 RNA-guided endonuclease",
                "voice_line": "Today, precision CRISPR gene editing allows scientists to correct hereditary genetic flaws at the single-nucleotide level.",
            },
        ],
    },
]

# Quick lookup by ID
_TOPIC_BY_ID: dict[str, dict[str, Any]] = {t["id"]: t for t in KNOWLEDGE_TOPICS}


def list_topic_ids() -> list[str]:
    """Return all available knowledge topic IDs."""
    return [t["id"] for t in KNOWLEDGE_TOPICS]


def list_domains() -> list[str]:
    """Return unique domains available in knowledge content."""
    return sorted({t["domain"] for t in KNOWLEDGE_TOPICS})


def get_topic_by_id(topic_id: str) -> dict[str, Any] | None:
    """Retrieve structured topic data by its ID."""
    return _TOPIC_BY_ID.get(topic_id)


def build_knowledge_topic(
    seed: int,
    duration: float,
    *,
    domain: str | None = None,
    topic_id: str | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Select and build a complete informative lesson structure synchronized to duration.

    - Splits duration evenly across 4 narrative segments
    - Assigns time boundaries [t0, t1]
    - Returns a deep copy enriched with seed and timing metadata
    """
    rng = np.random.default_rng(seed)

    if topic_id and topic_id in _TOPIC_BY_ID:
        chosen = _TOPIC_BY_ID[topic_id]
    elif domain and domain != "all":
        matching = [t for t in KNOWLEDGE_TOPICS if t["domain"] == domain]
        if matching:
            chosen = matching[rng.integers(0, len(matching))]
        else:
            chosen = KNOWLEDGE_TOPICS[rng.integers(0, len(KNOWLEDGE_TOPICS))]
    else:
        chosen = KNOWLEDGE_TOPICS[rng.integers(0, len(KNOWLEDGE_TOPICS))]

    # Build timed segments across duration
    raw_segments = list(chosen["segments"])
    num_segs = max(1, len(raw_segments))
    step = 1.0 / num_segs

    timed_segments = []
    for i, seg in enumerate(raw_segments):
        t0 = i * step
        t1 = min(1.0, (i + 1) * step)
        timed_segments.append(
            {
                "index": i,
                "total_segments": num_segs,
                "t0": float(t0),
                "t1": float(t1),
                "phase": seg.get("phase", "FACT"),
                "headline": seg.get("headline", ""),
                "body": seg.get("body", ""),
                "data_point": seg.get("data_point", ""),
                "voice_line": seg.get("voice_line", ""),
            }
        )

    return {
        "id": chosen["id"],
        "domain": chosen["domain"],
        "domain_label": chosen.get("domain_label", chosen["domain"].upper()),
        "title": chosen["title"],
        "subtitle": chosen.get("subtitle", ""),
        "hook": chosen.get("hook", ""),
        "schematic_type": chosen.get("schematic_type", "spec_blueprint"),
        "metrics": list(chosen.get("metrics", [])),
        "duration": float(duration),
        "seed": int(seed),
        "segments": timed_segments,
    }
