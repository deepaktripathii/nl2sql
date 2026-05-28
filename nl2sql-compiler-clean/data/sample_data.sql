-- ──────────────────────────────────────────────────────────────
--  NL2SQL Compiler — Sample Data
--  Run AFTER schema.sql
-- ──────────────────────────────────────────────────────────────

USE nl2sql_db;

-- ── Departments ──────────────────────────────────────────────────
INSERT INTO departments (name, location) VALUES
  ('Engineering',    'Bangalore'),
  ('Marketing',      'Mumbai'),
  ('Human Resources','Delhi'),
  ('Finance',        'Hyderabad'),
  ('Sales',          'Chennai'),
  ('Product',        'Pune'),
  ('Operations',     'Kolkata');

-- ── Employees ────────────────────────────────────────────────────
INSERT INTO employees (first_name, last_name, email, hire_date, dept_id, job_title, salary) VALUES
  ('Arjun',   'Sharma',    'arjun.sharma@company.com',    '2019-03-15', 1, 'Senior Engineer',        120000),
  ('Priya',   'Patel',     'priya.patel@company.com',     '2020-07-01', 1, 'Software Engineer',       85000),
  ('Rahul',   'Gupta',     'rahul.gupta@company.com',     '2018-01-20', 2, 'Marketing Manager',       95000),
  ('Anjali',  'Singh',     'anjali.singh@company.com',    '2021-09-10', 3, 'HR Specialist',           70000),
  ('Vikram',  'Mehta',     'vikram.mehta@company.com',    '2017-06-05', 4, 'Finance Lead',           110000),
  ('Neha',    'Joshi',     'neha.joshi@company.com',      '2022-02-14', 5, 'Sales Executive',         65000),
  ('Rohan',   'Verma',     'rohan.verma@company.com',     '2020-11-30', 1, 'Backend Engineer',        90000),
  ('Kavya',   'Reddy',     'kavya.reddy@company.com',     '2019-08-22', 6, 'Product Manager',        105000),
  ('Suresh',  'Kumar',     'suresh.kumar@company.com',    '2021-04-18', 2, 'Digital Marketer',        75000),
  ('Divya',   'Nair',      'divya.nair@company.com',      '2023-01-09', 1, 'Junior Engineer',         60000),
  ('Amit',    'Tiwari',    'amit.tiwari@company.com',     '2016-09-01', 4, 'Chief Financial Officer', 200000),
  ('Pooja',   'Iyer',      'pooja.iyer@company.com',      '2022-06-20', 3, 'HR Manager',              88000),
  ('Karan',   'Malhotra',  'karan.malhotra@company.com',  '2018-12-12', 5, 'Regional Sales Manager', 130000),
  ('Sneha',   'Desai',     'sneha.desai@company.com',     '2023-03-25', 6, 'UX Designer',             80000),
  ('Rajesh',  'Bose',      'rajesh.bose@company.com',     '2015-07-14', 7, 'Operations Director',    155000);

-- Update manager_id
UPDATE departments SET manager_id = 1  WHERE name = 'Engineering';
UPDATE departments SET manager_id = 3  WHERE name = 'Marketing';
UPDATE departments SET manager_id = 12 WHERE name = 'Human Resources';
UPDATE departments SET manager_id = 11 WHERE name = 'Finance';
UPDATE departments SET manager_id = 13 WHERE name = 'Sales';
UPDATE departments SET manager_id = 8  WHERE name = 'Product';
UPDATE departments SET manager_id = 15 WHERE name = 'Operations';

-- ── Customers ────────────────────────────────────────────────────
INSERT INTO customers (first_name, last_name, email, city, country) VALUES
  ('Aditya',    'Shah',      'aditya.shah@gmail.com',       'Mumbai',    'India'),
  ('Meera',     'Pillai',    'meera.pillai@gmail.com',      'Chennai',   'India'),
  ('Sanjay',    'Rao',       'sanjay.rao@gmail.com',        'Bangalore', 'India'),
  ('Lakshmi',   'Iyengar',   'lakshmi.i@gmail.com',         'Hyderabad', 'India'),
  ('Tushar',    'Patil',     'tushar.patil@gmail.com',      'Pune',      'India'),
  ('Riya',      'Kapoor',    'riya.kapoor@gmail.com',       'Delhi',     'India'),
  ('Manish',    'Sinha',     'manish.sinha@gmail.com',      'Kolkata',   'India'),
  ('Deepa',     'Nambiar',   'deepa.nambiar@gmail.com',     'Kochi',     'India'),
  ('Vivek',     'Jain',      'vivek.jain@gmail.com',        'Ahmedabad', 'India'),
  ('Ananya',    'Chatterjee','ananya.c@gmail.com',          'Kolkata',   'India'),
  ('Nikhil',    'Dubey',     'nikhil.dubey@gmail.com',      'Jaipur',    'India'),
  ('Swetha',    'Menon',     'swetha.menon@gmail.com',      'Chennai',   'India'),
  ('Harish',    'Pandey',    'harish.pandey@gmail.com',     'Lucknow',   'India'),
  ('Preeti',    'Saxena',    'preeti.saxena@gmail.com',     'Noida',     'India'),
  ('Gaurav',    'Mishra',    'gaurav.mishra@gmail.com',     'Bhopal',    'India');

-- ── Products ─────────────────────────────────────────────────────
INSERT INTO products (name, category, price, stock_qty) VALUES
  ('Laptop Pro 15"',          'Electronics',  89999.00, 45),
  ('Wireless Keyboard',       'Electronics',   2499.00, 200),
  ('Ergonomic Mouse',         'Electronics',   1799.00, 150),
  ('27" 4K Monitor',          'Electronics',  34999.00, 30),
  ('Mechanical Keyboard',     'Electronics',   4999.00, 80),
  ('USB-C Hub 7-in-1',        'Electronics',   2999.00, 120),
  ('Noise-Cancelling Headset','Electronics',  12999.00, 60),
  ('Desk Lamp LED',           'Furniture',     1499.00, 90),
  ('Adjustable Desk',         'Furniture',    18999.00, 20),
  ('Office Chair Ergonomic',  'Furniture',    14999.00, 35),
  ('Notebook 200 pages',      'Stationery',     199.00, 500),
  ('Ballpoint Pen Set (10)',   'Stationery',     299.00, 300),
  ('Whiteboard A1',           'Stationery',    2999.00, 40),
  ('Coffee Mug Insulated',    'Kitchen',        799.00, 180),
  ('Standing Desk Converter', 'Furniture',     8999.00, 25);

-- ── Orders ───────────────────────────────────────────────────────
INSERT INTO orders (customer_id, order_date, status, total_amount) VALUES
  (1,  '2024-01-05 10:15:00', 'delivered',   92498.00),
  (2,  '2024-01-12 14:30:00', 'delivered',   37498.00),
  (3,  '2024-02-03 09:45:00', 'delivered',    4298.00),
  (4,  '2024-02-18 16:00:00', 'shipped',     15798.00),
  (5,  '2024-03-01 11:20:00', 'delivered',   90998.00),
  (6,  '2024-03-15 13:00:00', 'processing',  27998.00),
  (7,  '2024-03-22 08:30:00', 'pending',      2998.00),
  (8,  '2024-04-05 15:45:00', 'delivered',   14999.00),
  (9,  '2024-04-18 12:10:00', 'shipped',      8999.00),
  (10, '2024-05-02 10:00:00', 'delivered',   47498.00),
  (1,  '2024-05-20 14:15:00', 'delivered',    3298.00),
  (3,  '2024-06-08 09:00:00', 'cancelled',    1799.00),
  (5,  '2024-06-25 17:30:00', 'delivered',   12999.00),
  (11, '2024-07-10 11:00:00', 'delivered',   24998.00),
  (12, '2024-07-22 13:45:00', 'shipped',     35998.00),
  (2,  '2024-08-05 10:30:00', 'delivered',    4699.00),
  (6,  '2024-08-19 15:00:00', 'processing',  90999.00),
  (13, '2024-09-03 09:15:00', 'delivered',    2499.00),
  (14, '2024-09-17 14:00:00', 'delivered',   15799.00),
  (15, '2024-10-01 11:30:00', 'pending',      8999.00);

-- ── Order Items ──────────────────────────────────────────────────
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
  (1,  1,  1, 89999.00),  -- Laptop
  (1,  2,  1,  2499.00),  -- Keyboard
  (2,  4,  1, 34999.00),  -- Monitor
  (2,  3,  1,  1799.00),  -- Mouse
  (2,  6,  1,  2999.00),  -- Hub (wrong subtotal in order – demo data)
  (3,  5,  1,  4999.00),  -- Mech keyboard
  (3,  12, 1,   299.00),
  (4,  10, 1, 14999.00),  -- Chair
  (4,  8,  1,  1499.00),
  (5,  1,  1, 89999.00),
  (5,  7,  1, 12999.00),
  (6,  9,  1, 18999.00),  -- Desk
  (6,  10, 1, 14999.00),
  (7,  14, 3,   799.00),  -- Coffee mugs
  (8,  10, 1, 14999.00),
  (9,  15, 1,  8999.00),
  (10, 1,  1, 89999.00), -- typo in total but fine for demo
  (10, 7,  1, 12999.00),
  (11, 12, 5,   299.00),
  (11, 11, 3,   199.00),
  (13, 7,  1, 12999.00),
  (14, 2,  2,  2499.00),
  (14, 3,  2,  1799.00),
  (15, 4,  1, 34999.00),
  (15, 6,  1,  2999.00),
  (16, 5,  1,  4999.00),
  (17, 1,  1, 89999.00),
  (18, 2,  1,  2499.00),
  (19, 4,  1, 34999.00),
  (20, 15, 1,  8999.00);

-- ── Salaries ─────────────────────────────────────────────────────
INSERT INTO salaries (employee_id, amount, effective) VALUES
  (1,  100000, '2019-03-15'), (1,  110000, '2021-04-01'), (1,  120000, '2023-04-01'),
  (2,   75000, '2020-07-01'), (2,   85000, '2022-07-01'),
  (3,   85000, '2018-01-20'), (3,   95000, '2020-06-01'),
  (4,   65000, '2021-09-10'), (4,   70000, '2023-09-01'),
  (5,   95000, '2017-06-05'), (5,  110000, '2021-06-01'),
  (6,   55000, '2022-02-14'), (6,   65000, '2024-01-01'),
  (7,   80000, '2020-11-30'), (7,   90000, '2023-01-01'),
  (8,   90000, '2019-08-22'), (8,  105000, '2022-08-01'),
  (9,   68000, '2021-04-18'), (9,   75000, '2023-04-01'),
  (10,  60000, '2023-01-09'),
  (11, 180000, '2016-09-01'), (11, 200000, '2022-01-01'),
  (12,  78000, '2022-06-20'), (12,  88000, '2024-01-01'),
  (13, 115000, '2018-12-12'), (13, 130000, '2022-01-01'),
  (14,  70000, '2023-03-25'), (14,  80000, '2024-03-01'),
  (15, 140000, '2015-07-14'), (15, 155000, '2021-07-01');
