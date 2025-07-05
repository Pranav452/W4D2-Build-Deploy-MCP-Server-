#!/usr/bin/env python3
"""
Script to populate the database with sample documents for testing the Document Analyzer
"""

from sqlmodel import Session
from models import Document, create_db_and_tables, engine
from datetime import datetime


def create_sample_documents():
    """Create sample documents for testing"""
    
    sample_documents = [
        {
            "title": "The Future of Artificial Intelligence",
            "content": """
            Artificial intelligence has transformed from a science fiction concept into a revolutionary technology that is reshaping our world. Machine learning algorithms now power everything from search engines to autonomous vehicles, demonstrating unprecedented capabilities in pattern recognition and decision-making. 

            The recent breakthroughs in deep learning have enabled computers to perform tasks that were once thought impossible. Neural networks can now understand natural language, recognize complex images, and even generate creative content. These developments are not just technological achievements; they represent a fundamental shift in how we interact with computers and process information.

            However, this rapid advancement brings both opportunities and challenges. While AI can enhance productivity and solve complex problems, it also raises important questions about privacy, job displacement, and ethical considerations. The future of AI depends on our ability to harness its power while addressing these concerns through thoughtful regulation and responsible development.
            """,
            "author": "Dr. Sarah Chen",
            "category": "Technology"
        },
        {
            "title": "Climate Change and Environmental Sustainability",
            "content": """
            Climate change represents one of the most pressing challenges of our time. Rising global temperatures, melting ice caps, and extreme weather events are clear indicators that our planet is undergoing significant environmental changes. The scientific consensus is overwhelming: human activities, particularly greenhouse gas emissions, are the primary drivers of these changes.

            The consequences of climate change extend far beyond environmental impacts. Economic systems, food security, and social stability are all at risk. Coastal communities face rising sea levels, while agricultural regions struggle with changing precipitation patterns and extreme weather events. These challenges disproportionately affect vulnerable populations, creating new forms of inequality and displacement.

            Despite these daunting challenges, there is reason for hope. Renewable energy technologies are becoming increasingly cost-effective, and many countries are committing to ambitious carbon reduction targets. Innovation in clean technology, coupled with changes in consumer behavior and policy reforms, offers a path toward a more sustainable future.
            """,
            "author": "Prof. Michael Rodriguez",
            "category": "Environment"
        },
        {
            "title": "The Art of Mindful Living",
            "content": """
            In our fast-paced world, the practice of mindfulness has emerged as a powerful tool for finding peace and clarity. Mindful living involves paying attention to the present moment without judgment, allowing us to experience life more fully and respond to challenges with greater wisdom and compassion.

            The benefits of mindfulness are well-documented and far-reaching. Regular practice can reduce stress, improve focus, enhance emotional regulation, and strengthen relationships. By cultivating awareness of our thoughts and feelings, we can break free from automatic reactions and make more conscious choices about how we live our lives.

            Implementing mindfulness doesn't require dramatic lifestyle changes. Simple practices like mindful breathing, walking meditation, or taking moments to truly savor our food can make a significant difference. The key is consistency and patience, allowing ourselves to develop this skill gradually over time.
            """,
            "author": "Lisa Thompson",
            "category": "Wellness"
        },
        {
            "title": "The Digital Revolution in Education",
            "content": """
            The educational landscape is undergoing a profound transformation driven by digital technologies. Online learning platforms, interactive educational software, and virtual classrooms are changing how knowledge is delivered and consumed. This digital revolution has accelerated dramatically, particularly in response to global challenges that have made traditional classroom learning difficult.

            Technology offers unprecedented opportunities for personalized learning experiences. Adaptive learning systems can adjust content difficulty based on individual progress, while multimedia resources cater to different learning styles. Students can access vast libraries of information, collaborate with peers globally, and receive immediate feedback on their work.

            However, the digital divide remains a significant challenge. Not all students have equal access to technology and high-speed internet, creating disparities in educational opportunities. Additionally, the shift to digital learning requires new skills from both educators and students, highlighting the importance of digital literacy and ongoing professional development.
            """,
            "author": "Dr. James Park",
            "category": "Education"
        },
        {
            "title": "The Psychology of Habit Formation",
            "content": """
            Understanding how habits form and persist is crucial for anyone seeking to make positive changes in their life. Habits are automatic behaviors that our brains develop to conserve energy and streamline decision-making. The habit loop consists of three key components: a cue that triggers the behavior, the routine or behavior itself, and the reward that reinforces the pattern.

            Research in neuroscience reveals that habits are literally carved into our brains through repeated actions. The basal ganglia, a region associated with automatic behaviors, becomes increasingly active as behaviors become more habitual. This explains why habits can feel effortless once established but also why they can be so difficult to break.

            Successful habit change requires strategic intervention at each stage of the habit loop. By identifying triggers, substituting new routines, and ensuring rewarding outcomes, we can gradually reshape our behavioral patterns. The key is to start small, be consistent, and celebrate progress along the way.
            """,
            "author": "Dr. Amanda Foster",
            "category": "Psychology"
        },
        {
            "title": "Sustainable Urban Planning for the Future",
            "content": """
            As urbanization continues to accelerate globally, the need for sustainable city planning has never been more urgent. By 2050, it's estimated that nearly 70% of the world's population will live in urban areas. This rapid growth presents both opportunities and challenges for creating livable, environmentally responsible cities.

            Sustainable urban planning involves designing cities that minimize environmental impact while maximizing quality of life for residents. This includes developing efficient public transportation systems, creating green spaces, implementing renewable energy infrastructure, and promoting mixed-use development that reduces the need for long commutes.

            Smart city technologies are playing an increasingly important role in sustainable urban development. Internet of Things sensors can monitor air quality and traffic patterns, while data analytics help optimize resource allocation. These technologies, combined with community engagement and forward-thinking policies, can help create cities that are both environmentally sustainable and economically viable.
            """,
            "author": "Carlos Mendez",
            "category": "Urban Planning"
        },
        {
            "title": "The Economics of Remote Work",
            "content": """
            The shift toward remote work has fundamentally altered the economic landscape for both employers and employees. This transformation, accelerated by recent global events, has created new opportunities and challenges that are reshaping traditional employment models.

            For employees, remote work offers increased flexibility, reduced commuting costs, and access to job opportunities regardless of geographic location. However, it also presents challenges such as social isolation, difficulty maintaining work-life balance, and potential impacts on career advancement. The economic benefits vary significantly based on individual circumstances and industry sectors.

            From an employer's perspective, remote work can reduce overhead costs and expand access to talent pools. Companies can save on office space, utilities, and other infrastructure costs while potentially increasing productivity and employee satisfaction. However, managing remote teams requires new skills and tools, and some organizations struggle with maintaining company culture and collaboration in distributed environments.
            """,
            "author": "Dr. Rachel Kim",
            "category": "Economics"
        },
        {
            "title": "Breakthrough in Quantum Computing",
            "content": """
            Quantum computing represents a paradigm shift in computational technology that could revolutionize fields ranging from cryptography to drug discovery. Unlike classical computers that process information in binary bits, quantum computers use quantum bits or qubits that can exist in multiple states simultaneously, enabling exponentially faster processing for certain types of problems.

            Recent breakthroughs have brought quantum computing closer to practical applications. Researchers have demonstrated quantum supremacy in specific computational tasks, showing that quantum computers can solve certain problems faster than the world's most powerful classical computers. Major technology companies and governments are investing billions of dollars in quantum research and development.

            The implications of quantum computing are profound and far-reaching. In cryptography, quantum computers could break current encryption methods, necessitating the development of quantum-resistant security protocols. In drug discovery, they could simulate molecular interactions at unprecedented scales, accelerating the development of new medicines. The race to achieve practical quantum advantage is intensifying, with significant implications for global competitiveness and security.
            """,
            "author": "Dr. Kevin Zhang",
            "category": "Technology"
        },
        {
            "title": "The Philosophy of Ethical Decision Making",
            "content": """
            Ethical decision-making is a fundamental aspect of human existence that shapes our relationships, communities, and society as a whole. Throughout history, philosophers have developed various frameworks for understanding what makes an action morally right or wrong, each offering unique insights into the nature of ethics and human behavior.

            Utilitarianism, developed by philosophers like Jeremy Bentham and John Stuart Mill, suggests that the moral worth of an action is determined by its consequences. According to this view, we should act in ways that maximize overall happiness or well-being for the greatest number of people. This consequentialist approach has influenced many areas of policy and decision-making.

            Deontological ethics, exemplified by Immanuel Kant's categorical imperative, focuses on the inherent rightness or wrongness of actions rather than their consequences. Kant argued that we should act only according to principles that we could will to be universal laws. This approach emphasizes duty, respect for persons, and the importance of moral rules that apply regardless of context.

            Virtue ethics, tracing back to Aristotle, concentrates on character rather than actions or consequences. This approach asks not "What should I do?" but "What kind of person should I be?" Virtue ethicists argue that cultivating virtues like courage, honesty, and compassion naturally leads to ethical behavior.
            """,
            "author": "Prof. Elizabeth Harper",
            "category": "Philosophy"
        },
        {
            "title": "The Science of Sleep and Dreams",
            "content": """
            Sleep is one of the most mysterious and essential aspects of human biology. Despite spending approximately one-third of our lives asleep, scientists are still uncovering the complex mechanisms that govern sleep and its crucial role in physical and mental health.

            During sleep, our brains undergo remarkable transformations. The glymphatic system becomes highly active, clearing toxins and waste products that accumulate during waking hours. Memory consolidation occurs as the brain processes and stores information from the day, transferring important memories from short-term to long-term storage. Different sleep stages serve distinct functions, from physical restoration during deep sleep to emotional processing during REM sleep.

            Dreams, occurring primarily during REM sleep, remain one of the most intriguing aspects of sleep science. While their exact purpose is still debated, research suggests that dreams may play important roles in memory consolidation, emotional regulation, and creative problem-solving. Some studies indicate that people who remember their dreams tend to have better emotional intelligence and creative abilities.

            The modern world presents numerous challenges to healthy sleep patterns. Artificial light, particularly blue light from screens, can disrupt circadian rhythms and delay sleep onset. Chronic sleep deprivation has been linked to numerous health problems, including obesity, diabetes, cardiovascular disease, and mental health disorders.
            """,
            "author": "Dr. Jennifer Walsh",
            "category": "Health"
        },
        {
            "title": "The Cultural Impact of Social Media",
            "content": """
            Social media platforms have fundamentally transformed how we communicate, share information, and perceive the world around us. These digital spaces have created new forms of social interaction while simultaneously challenging traditional notions of privacy, authenticity, and community.

            The democratization of information sharing has empowered individuals to become content creators and citizen journalists. Social movements can now organize and spread awareness at unprecedented speeds, as seen in various global campaigns for social justice. However, this same technology has also facilitated the spread of misinformation and created echo chambers that can reinforce existing beliefs and polarize communities.

            The psychological impact of social media is complex and multifaceted. While these platforms can foster connection and support networks, they can also contribute to anxiety, depression, and feelings of inadequacy through constant social comparison. The curated nature of social media content often presents unrealistic standards of success and happiness, particularly affecting young people who have grown up in the digital age.

            As social media continues to evolve, society must grapple with questions about regulation, digital literacy, and the balance between connectivity and well-being. Understanding these platforms' cultural impact is crucial for navigating the digital age thoughtfully and responsibly.
            """,
            "author": "Dr. Maya Patel",
            "category": "Sociology"
        },
        {
            "title": "Innovations in Renewable Energy",
            "content": """
            The renewable energy sector is experiencing unprecedented growth and innovation, driven by technological advances, environmental concerns, and economic factors. Solar, wind, and other clean energy technologies are becoming increasingly cost-competitive with fossil fuels, marking a significant shift in the global energy landscape.

            Solar energy has seen remarkable progress in efficiency and affordability. Photovoltaic cells are becoming more efficient at converting sunlight into electricity, while manufacturing costs continue to decline. Innovative applications include solar panels integrated into building materials, floating solar farms, and concentrated solar power systems that can store energy for use when the sun isn't shining.

            Wind energy is also advancing rapidly, with larger and more efficient turbines capable of generating power even in low-wind conditions. Offshore wind farms are expanding globally, taking advantage of stronger and more consistent winds over water. Additionally, advances in energy storage technology are addressing the intermittency challenges associated with renewable energy sources.

            Emerging technologies such as green hydrogen production, advanced battery systems, and smart grid infrastructure are creating new possibilities for renewable energy integration. These innovations are not only making clean energy more reliable and efficient but also creating new economic opportunities and jobs in the growing green economy.
            """,
            "author": "Dr. Thomas Anderson",
            "category": "Energy"
        },
        {
            "title": "The Art and Science of Cooking",
            "content": """
            Cooking is a unique blend of art and science that engages all our senses and connects us to our cultural heritage. The transformation of raw ingredients into delicious meals involves complex chemical reactions, precise timing, and creative expression. Understanding the science behind cooking can elevate our culinary skills and appreciation for this fundamental human activity.

            The Maillard reaction, responsible for the browning and flavor development in cooked foods, is one of the most important chemical processes in cooking. This reaction between amino acids and sugars creates hundreds of flavor compounds that give grilled meats, toasted bread, and roasted coffee their distinctive tastes and aromas. Temperature control and timing are crucial for achieving optimal results.

            Heat transfer is another fundamental aspect of cooking science. Conduction, convection, and radiation each play roles in how food cooks, and understanding these principles can help explain why certain cooking methods work better for specific ingredients. For example, the high heat of a cast-iron pan creates excellent searing through conduction, while the gentle circulation of air in a convection oven cooks food more evenly.

            Beyond the technical aspects, cooking is deeply cultural and creative. Traditional recipes pass down cultural knowledge and family history, while modern cuisine constantly evolves through experimentation and fusion. The act of cooking and sharing meals strengthens social bonds and creates lasting memories, making it far more than just sustenance.
            """,
            "author": "Chef Isabella Rodriguez",
            "category": "Culinary Arts"
        },
        {
            "title": "The Future of Transportation",
            "content": """
            Transportation is undergoing a revolutionary transformation that will reshape how we move people and goods around the world. Electric vehicles, autonomous driving technology, and new forms of urban mobility are converging to create a more sustainable and efficient transportation ecosystem.

            Electric vehicles are rapidly gaining market share as battery technology improves and charging infrastructure expands. The environmental benefits are significant, particularly when powered by renewable energy sources. Major automakers are committing to all-electric lineups within the next decade, while governments worldwide are implementing policies to accelerate the transition away from fossil fuel vehicles.

            Autonomous driving technology promises to improve road safety, reduce traffic congestion, and provide mobility options for people who cannot drive traditional vehicles. While fully autonomous vehicles are still in development, advanced driver assistance systems are already making roads safer. The integration of artificial intelligence and sensor technology continues to advance, bringing us closer to widespread autonomous transportation.

            Urban mobility is also evolving with the rise of ride-sharing, electric scooters, and micro-mobility solutions. Cities are redesigning infrastructure to accommodate these new forms of transportation while promoting walking and cycling. The concept of Mobility as a Service (MaaS) integrates various transportation options into seamless, user-friendly platforms.
            """,
            "author": "Dr. Robert Chang",
            "category": "Transportation"
        },
        {
            "title": "The Power of Storytelling in Human Culture",
            "content": """
            Storytelling is one of humanity's most powerful tools for communication, education, and cultural preservation. From ancient oral traditions to modern digital media, stories shape our understanding of the world and our place within it. The ability to craft and share narratives is fundamental to human experience and social cohesion.

            Stories serve multiple functions in human society. They transmit cultural values and knowledge across generations, helping preserve important traditions and lessons. Through narratives, we can explore complex emotions and situations in a safe environment, developing empathy and understanding for diverse perspectives. Stories also provide meaning and structure to our experiences, helping us make sense of chaos and uncertainty.

            The neuroscience of storytelling reveals why narratives are so compelling and memorable. When we hear a story, multiple areas of our brain activate, including regions associated with sensory experience, emotion, and motor function. This neural engagement makes stories more memorable than abstract information and explains why narrative-based learning is so effective.

            In the digital age, storytelling has evolved to include interactive and multimedia elements. Video games, virtual reality experiences, and social media platforms offer new ways to tell and experience stories. However, the fundamental human need for narrative remains unchanged, demonstrating the enduring power of storytelling across all cultures and time periods.
            """,
            "author": "Dr. Sarah Mitchell",
            "category": "Literature"
        },
        {
            "title": "The Mathematics of Music",
            "content": """
            Music and mathematics share a profound and beautiful relationship that has fascinated scholars for millennia. From the harmonic ratios discovered by Pythagoras to the complex algorithms used in modern music production, mathematical principles underlie many aspects of musical creation and appreciation.

            The physics of sound waves provides the foundation for understanding how music works. Frequency determines pitch, with doubling a frequency creating an octave. The mathematical relationships between frequencies create the harmonic series, which forms the basis of musical scales and chord progressions. These ratios, such as 3:2 for a perfect fifth or 4:3 for a perfect fourth, create the consonant intervals that sound pleasing to the human ear.

            Rhythm and meter in music are fundamentally mathematical concepts involving patterns, fractions, and timing. Time signatures divide music into measurable units, while polyrhythms create complex patterns by layering different rhythmic cycles. Composers throughout history have used mathematical concepts like golden ratio proportions and geometric patterns to structure their works.

            Modern technology has expanded the mathematical aspects of music creation. Digital audio processing relies on complex algorithms for effects, synthesis, and analysis. Machine learning and artificial intelligence are being used to compose music, analyze musical styles, and even predict what songs might become popular. These developments continue to blur the lines between mathematical precision and artistic expression.
            """,
            "author": "Prof. David Chen",
            "category": "Music"
        },
        {
            "title": "The Importance of Biodiversity Conservation",
            "content": """
            Biodiversity, the variety of life on Earth, is facing unprecedented threats from human activities. The current rate of species extinction is estimated to be 100 to 1,000 times higher than natural background rates, leading scientists to declare that we are in the midst of the sixth mass extinction event. Understanding and protecting biodiversity is crucial for maintaining healthy ecosystems and ensuring human survival.

            Ecosystems depend on complex networks of interactions between species. Each organism plays a specific role, and the loss of even seemingly insignificant species can have cascading effects throughout the system. Pollinators like bees and butterflies are essential for plant reproduction and food production, while predators help control prey populations and maintain ecological balance.

            The economic value of biodiversity is enormous, though often underestimated. Ecosystem services such as pollination, water purification, climate regulation, and disease control provide trillions of dollars in value annually. Many medicines are derived from natural compounds found in plants and animals, and genetic diversity in crops is essential for food security.

            Conservation efforts must address multiple threats simultaneously, including habitat destruction, climate change, pollution, and invasive species. Protected areas, restoration projects, and sustainable land use practices are all important strategies. However, successful conservation requires global cooperation and recognition that human well-being is inextricably linked to the health of natural ecosystems.
            """,
            "author": "Dr. Maria Santos",
            "category": "Conservation"
        },
        {
            "title": "The History and Future of Space Exploration",
            "content": """
            Space exploration represents humanity's greatest adventure, pushing the boundaries of technology, science, and human endurance. From the first satellite launches to Mars rovers and plans for lunar bases, our journey into space has yielded incredible discoveries and technological innovations that benefit life on Earth.

            The space race of the 20th century drove rapid technological advancement and international competition. The achievements of early space programs, from Sputnik to the Apollo moon landings, demonstrated human ingenuity and determination. These missions not only advanced our understanding of space but also led to innovations in computing, materials science, and telecommunications that transformed modern life.

            Today's space exploration is characterized by international cooperation and private sector involvement. The International Space Station serves as a platform for scientific research and international collaboration. Private companies are developing reusable rockets, reducing launch costs and making space more accessible. Commercial space travel is becoming reality, opening new possibilities for tourism and research.

            The future of space exploration holds exciting possibilities. Plans for permanent lunar bases could serve as stepping stones to Mars exploration. Robotic missions continue to explore the outer solar system, searching for signs of life and studying planetary formation. Advanced propulsion technologies under development could enable faster travel to distant destinations, potentially revolutionizing our understanding of the universe.
            """,
            "author": "Dr. Alex Johnson",
            "category": "Space Science"
        }
    ]
    
    # Create database and tables
    create_db_and_tables()
    
    # Add documents to database
    with Session(engine) as session:
        for doc_data in sample_documents:
            document = Document(**doc_data)
            session.add(document)
        
        session.commit()
        print(f"Successfully added {len(sample_documents)} sample documents to the database!")


if __name__ == "__main__":
    create_sample_documents() 