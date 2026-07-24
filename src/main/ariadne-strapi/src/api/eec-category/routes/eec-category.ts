/**
 * $api router
 */

export default {
  routes: [
    {
      method: 'GET',
      path: '/eec-category',
      handler: 'eec-category.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/eec-category/:id',
      handler: 'eec-category.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/eec-category',
      handler: 'eec-category.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/eec-category/:id',
      handler: 'eec-category.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/eec-category/:id',
      handler: 'eec-category.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
