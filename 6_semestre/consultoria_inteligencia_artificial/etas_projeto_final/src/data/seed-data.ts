/**
 * Dados seed para restaurantes, produtos e clientes
 */

import { Restaurant, Product, Customer } from '../lib/local-storage';

export const restaurants: Restaurant[] = [
  {
    id: 'rest_1',
    name: 'Pizzaria Bella Napoli',
    lat: -23.5505,
    lon: -46.6333,
    avg_prep_time_min: 25
  },
  {
    id: 'rest_2', 
    name: 'Burger Master',
    lat: -23.5489,
    lon: -46.6388,
    avg_prep_time_min: 15
  },
  {
    id: 'rest_3',
    name: 'Sushi Tokyo',
    lat: -23.5558,
    lon: -46.6396,
    avg_prep_time_min: 30
  },
  {
    id: 'rest_4',
    name: 'Pasta e Vino',
    lat: -23.5629,
    lon: -46.6544,
    avg_prep_time_min: 20
  },
  {
    id: 'rest_5',
    name: 'Taco Loco',
    lat: -23.5475,
    lon: -46.6361,
    avg_prep_time_min: 18
  }
];

export const products: Product[] = [
  // Pizzaria Bella Napoli
  { id: 'prod_1', restaurant_id: 'rest_1', name: 'Pizza Margherita', price: 42.00, additional_prep_min: 5 },
  { id: 'prod_2', restaurant_id: 'rest_1', name: 'Pizza Calabresa', price: 45.00, additional_prep_min: 5 },
  { id: 'prod_3', restaurant_id: 'rest_1', name: 'Pizza Quatro Queijos', price: 48.00, additional_prep_min: 7 },
  { id: 'prod_4', restaurant_id: 'rest_1', name: 'Pizza Portuguesa', price: 50.00, additional_prep_min: 8 },
  { id: 'prod_5', restaurant_id: 'rest_1', name: 'Pizza Pepperoni', price: 47.00, additional_prep_min: 6 },
  
  // Burger Master
  { id: 'prod_6', restaurant_id: 'rest_2', name: 'Classic Burger', price: 28.00, additional_prep_min: 3 },
  { id: 'prod_7', restaurant_id: 'rest_2', name: 'Bacon Burger', price: 32.00, additional_prep_min: 4 },
  { id: 'prod_8', restaurant_id: 'rest_2', name: 'Veggie Burger', price: 26.00, additional_prep_min: 3 },
  { id: 'prod_9', restaurant_id: 'rest_2', name: 'Double Cheese', price: 35.00, additional_prep_min: 5 },
  { id: 'prod_10', restaurant_id: 'rest_2', name: 'Chicken Burger', price: 30.00, additional_prep_min: 4 },
  
  // Sushi Tokyo
  { id: 'prod_11', restaurant_id: 'rest_3', name: 'Combo Salmão', price: 65.00, additional_prep_min: 10 },
  { id: 'prod_12', restaurant_id: 'rest_3', name: 'Combo Especial', price: 85.00, additional_prep_min: 15 },
  { id: 'prod_13', restaurant_id: 'rest_3', name: 'Hot Roll', price: 45.00, additional_prep_min: 8 },
  { id: 'prod_14', restaurant_id: 'rest_3', name: 'Temaki Salmão', price: 18.00, additional_prep_min: 5 },
  { id: 'prod_15', restaurant_id: 'rest_3', name: 'Sashimi Variado', price: 75.00, additional_prep_min: 12 },
  
  // Pasta e Vino
  { id: 'prod_16', restaurant_id: 'rest_4', name: 'Carbonara', price: 38.00, additional_prep_min: 5 },
  { id: 'prod_17', restaurant_id: 'rest_4', name: 'Bolognese', price: 35.00, additional_prep_min: 5 },
  { id: 'prod_18', restaurant_id: 'rest_4', name: 'Pesto', price: 40.00, additional_prep_min: 6 },
  { id: 'prod_19', restaurant_id: 'rest_4', name: 'Lasanha', price: 42.00, additional_prep_min: 8 },
  { id: 'prod_20', restaurant_id: 'rest_4', name: 'Fettuccine Alfredo', price: 36.00, additional_prep_min: 5 },
  
  // Taco Loco
  { id: 'prod_21', restaurant_id: 'rest_5', name: 'Tacos de Carne', price: 32.00, additional_prep_min: 4 },
  { id: 'prod_22', restaurant_id: 'rest_5', name: 'Tacos de Frango', price: 30.00, additional_prep_min: 4 },
  { id: 'prod_23', restaurant_id: 'rest_5', name: 'Burrito Supreme', price: 38.00, additional_prep_min: 6 },
  { id: 'prod_24', restaurant_id: 'rest_5', name: 'Quesadilla', price: 25.00, additional_prep_min: 3 },
  { id: 'prod_25', restaurant_id: 'rest_5', name: 'Nachos Especiais', price: 28.00, additional_prep_min: 5 }
];

export const customers: Customer[] = [
  { 
    id: 'cust_1', 
    name: 'Ana Silva', 
    lat: -23.5612, 
    lon: -46.6556, 
    whatsapp_phone: '+5511987654321' 
  },
  { 
    id: 'cust_2', 
    name: 'Carlos Santos', 
    lat: -23.5432, 
    lon: -46.6289, 
    whatsapp_phone: '+5511976543210' 
  },
  { 
    id: 'cust_3', 
    name: 'Beatriz Costa', 
    lat: -23.5689, 
    lon: -46.6512, 
    whatsapp_phone: '+5511965432109' 
  },
  { 
    id: 'cust_4', 
    name: 'Diego Oliveira', 
    lat: -23.5523, 
    lon: -46.6445, 
    whatsapp_phone: '+5511954321098' 
  },
  { 
    id: 'cust_5', 
    name: 'Elena Rodrigues', 
    lat: -23.5456, 
    lon: -46.6378, 
    whatsapp_phone: '+5511943210987' 
  },
  { 
    id: 'cust_6', 
    name: 'Fernando Lima', 
    lat: -23.5578, 
    lon: -46.6489, 
    whatsapp_phone: '+5511932109876' 
  },
  { 
    id: 'cust_7', 
    name: 'Gabriela Alves', 
    lat: -23.5501, 
    lon: -46.6412, 
    whatsapp_phone: '+5511921098765' 
  },
  { 
    id: 'cust_8', 
    name: 'Hugo Martins', 
    lat: -23.5634, 
    lon: -46.6523, 
    whatsapp_phone: '+5511910987654' 
  },
  { 
    id: 'cust_9', 
    name: 'Isabella Santos', 
    lat: -23.5467, 
    lon: -46.6234, 
    whatsapp_phone: '+5511909876543' 
  },
  { 
    id: 'cust_10', 
    name: 'João Pedro', 
    lat: -23.5712, 
    lon: -46.6678, 
    whatsapp_phone: '+5511898765432' 
  }
];

// Helper functions para encontrar dados
export const getRestaurantById = (id: string): Restaurant | undefined => {
  return restaurants.find(r => r.id === id);
};

export const getProductById = (id: string): Product | undefined => {
  return products.find(p => p.id === id);
};

export const getCustomerById = (id: string): Customer | undefined => {
  return customers.find(c => c.id === id);
};

export const getProductsByRestaurant = (restaurantId: string): Product[] => {
  return products.filter(p => p.restaurant_id === restaurantId);
};

// Dados de exemplo para histórico
export const generateSampleOrders = () => {
  const sampleOrders = [];
  const statuses = ['preparing', 'in_route', 'delivered'] as const;
  
  for (let i = 0; i < 10; i++) {
    const randomRestaurant = restaurants[Math.floor(Math.random() * restaurants.length)];
    const randomCustomer = customers[Math.floor(Math.random() * customers.length)];
    const randomProducts = products
      .filter(p => p.restaurant_id === randomRestaurant.id)
      .slice(0, Math.floor(Math.random() * 3) + 1);
    
    const createdDate = new Date();
    createdDate.setDate(createdDate.getDate() - Math.floor(Math.random() * 7));
    
    const order = {
      id: `order_sample_${i + 1}`,
      customer_id: randomCustomer.id,
      restaurant_id: randomRestaurant.id,
      status: statuses[Math.floor(Math.random() * statuses.length)],
      predicted_eta_min: 30 + Math.floor(Math.random() * 30),
      actual_delivery_min: null,
      distance_km: 2 + Math.random() * 8,
      created_at: createdDate.toISOString(),
      delivered_at: null,
      items: randomProducts.map(p => ({
        id: `item_${i}_${p.id}`,
        product_id: p.id,
        quantity: Math.floor(Math.random() * 3) + 1,
        unit_price: p.price
      })),
      total_amount: randomProducts.reduce((sum, p) => sum + p.price, 0)
    };
    
    // Se o pedido está entregue, adiciona dados de entrega
    if (order.status === 'delivered') {
      const deliveredDate = new Date(createdDate);
      deliveredDate.setMinutes(deliveredDate.getMinutes() + order.predicted_eta_min + Math.floor(Math.random() * 20) - 10);
      order.delivered_at = deliveredDate.toISOString();
      order.actual_delivery_min = Math.round((deliveredDate.getTime() - createdDate.getTime()) / (1000 * 60));
    }
    
    sampleOrders.push(order);
  }
  
  return sampleOrders;
};