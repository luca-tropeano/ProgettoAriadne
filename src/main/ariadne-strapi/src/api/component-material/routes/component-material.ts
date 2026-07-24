/**
 * $api router
 */

export default {
  routes: [
    {
      method: 'GET',
      path: '/component-material',
      handler: 'component-material.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/component-material/:id',
      handler: 'component-material.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/component-material',
      handler: 'component-material.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/component-material/:id',
      handler: 'component-material.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/component-material/:id',
      handler: 'component-material.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
