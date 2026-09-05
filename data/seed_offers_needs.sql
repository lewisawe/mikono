-- Mikono — seed data
-- Deliberately written so the RIGHT matches share MEANING, not keywords.
-- e.g. "I repair computers" should match "our lab machines won't turn on"
-- even though no words overlap. That is the whole point of semantic matching.

USE DATABASE MIKONO;
USE SCHEMA CORE;
USE WAREHOUSE MIKONO_WH;

INSERT INTO OFFERS (offer_id, volunteer_name, location, availability, description) VALUES
(1, 'Amina',   'Nairobi',  'weekends',            'I fix broken laptops and desktops. Comfortable reinstalling operating systems and replacing failed hard drives.'),
(2, 'Brian',   'Nairobi',  'evenings after 6pm',  'I am a qualified accountant and can help small organisations get their books in order and prepare simple financial statements.'),
(3, 'Cynthia', 'Kisumu',   'Saturday mornings',   'Former primary school teacher. Happy to tutor children in maths and reading.'),
(4, 'David',   'Mombasa',  'flexible, remote',    'Graphic designer. I can make posters, flyers and social media graphics for a good cause, free of charge.'),
(5, 'Esther',  'Nairobi',  'weekday afternoons',  'Registered nurse. I can run basic health check-ups and talk to communities about hygiene and first aid.'),
(6, 'Felix',   'Nakuru',   'weekends',            'I build websites and can set up a simple online presence for a group that has none.'),
(7, 'Grace',   'Kisumu',   'any evening',         'I speak English, Swahili and Luo. Willing to translate documents or interpret at meetings.'),
(8, 'Hassan',  'Mombasa',  'mornings',            'I drive a pickup and can move furniture, equipment or supplies around town when needed.');

INSERT INTO NEEDS (need_id, org_name, location, urgency, description) VALUES
(1, 'Uhuru Primary School',      'Nairobi', 'this term',   'Our computer lab machines will not switch on and we cannot afford a technician. Children are missing their ICT lessons.'),
(2, 'Mama Watoto Childrens Home','Kisumu',  'ongoing',     'We would love someone to help our kids with schoolwork on weekends, especially numbers and reading.'),
(3, 'Green Streets Initiative',  'Nairobi', 'next month',  'We are a small volunteer group and have no way to tell people about our clean-up events. We need help looking professional online.'),
(4, 'Coastal Health Outreach',   'Mombasa', 'urgent',      'Planning a community day and need someone medical to do simple screenings and teach basic hygiene.'),
(5, 'Bookmark Literacy Trust',   'Nairobi', 'ongoing',     'Our donated books are in English but many families here read Swahili. We need help making them accessible.'),
(6, 'Furaha Womens Group',       'Nakuru',  'this month',  'We keep our savings records in a notebook and it is a mess. We need someone who understands money to help us sort it out.'),
(7, 'Harvest Food Bank',         'Mombasa', 'weekly',      'We receive food donations across town but struggle to collect and deliver them without transport.'),
(8, 'Sunrise Youth Centre',      'Nairobi', 'no rush',     'We want printed materials to promote our free skills classes but have no one who can design them.');
